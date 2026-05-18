"""
Auth Router — Fixed
====================
Fixes:
  1. Block TTL: 60 seconds (was 1 hour) — testing friendly
  2. Only block after 5 failed attempts from same IP
  3. Never block a SUCCESSFUL login — only block on confirmed attacks
  4. Successful logins clear the IP block and failure counter
"""

from fastapi import APIRouter, Request, HTTPException, Depends
from pydantic import BaseModel
import time
import json
import logging
import hashlib

import aiosqlite
from app.core.database import get_db
from app.ml.detector import SecurityDetector, LoginEvent

logger = logging.getLogger(__name__)
router = APIRouter()

BLOCK_DURATION_SECONDS = 60   # 1 minute for testing (change to 3600 for prod)
FAILED_ATTEMPTS_BEFORE_BLOCK = 5  # Allow 5 failed attempts before blocking

# ─── SCHEMAS ──────────────────────────────────────────────────────────────────
class LoginRequest(BaseModel):
    username: str
    password: str

class LoginResponse(BaseModel):
    success: bool
    message: str
    security: dict


# ─── VALID USERS ──────────────────────────────────────────────────────────────
VALID_USERS = {
    "admin": hashlib.sha256(b"admin123").hexdigest(),
    "alice": hashlib.sha256(b"alice_pass").hexdigest(),
    "bob":   hashlib.sha256(b"bob_secure").hexdigest(),
}

def _check_password(username: str, password: str) -> bool:
    stored = VALID_USERS.get(username.strip().lower())
    if not stored:
        return False
    return stored == hashlib.sha256(password.encode()).hexdigest()

def _get_client_ip(request: Request) -> str:
    forwarded = request.headers.get("X-Forwarded-For")
    if forwarded:
        return forwarded.split(",")[0].strip()
    if request.client:
        return request.client.host
    return "0.0.0.0"


# ─── LOGIN ENDPOINT ────────────────────────────────────────────────────────────
@router.post("/login", response_model=LoginResponse)
async def login(
    body: LoginRequest,
    request: Request,
    db: aiosqlite.Connection = Depends(get_db),
):
    ip  = _get_client_ip(request)
    ua  = request.headers.get("User-Agent", "")
    now = time.time()

    # 1. Check if IP is currently blocked
    async with db.execute(
        "SELECT reason, expires_at FROM blocked_ips WHERE ip = ? AND (expires_at IS NULL OR expires_at > ?)",
        (ip, now),
    ) as cur:
        blocked_row = await cur.fetchone()

    if blocked_row:
        remaining = int(blocked_row["expires_at"] - now) if blocked_row["expires_at"] else 0
        raise HTTPException(
            status_code=429,
            detail=f"IP temporarily blocked ({blocked_row['reason']}). Auto-unblocks in {remaining}s."
        )

    # 2. Authenticate
    success = _check_password(body.username, body.password)

    # 3. Build event
    pw_fingerprint = "CORRECT" if success else body.password[:20]
    event = LoginEvent(
        ip_address=ip,
        username=body.username,
        success=success,
        user_agent=ua,
        password_hint=pw_fingerprint,
        timestamp=now,
    )

    # 4. AI/ML analysis — never flag successful logins as attacks
    detector: SecurityDetector = request.app.state.detector

    if success:
        # Clear brute-force memory and block for this IP on success
        detector.failure_tracker._data.pop(ip, None)
        detector.request_tracker._data.pop(ip, None)
        
        # Remove IP from blocked_ips on successful login
        await db.execute("DELETE FROM blocked_ips WHERE ip = ?", (ip,))
        
        attack_type  = "none"
        severity     = "low"
        risk_score   = 0.0
        reasons      = []
        should_block = False
        # Feed to ML baseline only
        await detector.analyze_login(event)
    else:
        result = await detector.analyze_login(event)
        attack_type  = result.attack_type
        severity     = result.severity
        risk_score   = result.risk_score
        reasons      = result.reasons
        should_block = False  # Reset to False, decide below based on count
        
        # Count failed attempts from this IP in the last BLOCK_DURATION_SECONDS
        async with db.execute(
            "SELECT COUNT(*) as count FROM login_attempts WHERE ip_address = ? AND success = 0 AND timestamp > ?",
            (ip, now - BLOCK_DURATION_SECONDS),
        ) as cur:
            row = await cur.fetchone()
            failed_count = row["count"] + 1  # +1 for current attempt (about to be logged)
        
        # Block if:
        # 1. Pattern-based attack detected (SQLi, XSS, etc.) OR
        # 2. Brute force threshold reached (5+ failures)
        if result.should_block and attack_type in ("sqli", "xss", "cmd_injection", "path_traversal"):
            # Pattern-based attacks: block immediately
            should_block = True
        elif failed_count >= FAILED_ATTEMPTS_BEFORE_BLOCK:
            # Brute force: block after threshold
            should_block = True
            attack_type = "brute_force" if attack_type == "none" else attack_type

    # 5. Auto-block only if threshold is reached
    if should_block:
        await db.execute(
            "INSERT OR REPLACE INTO blocked_ips (ip, reason, blocked_at, expires_at) VALUES (?, ?, ?, ?)",
            (ip, attack_type, now, now + BLOCK_DURATION_SECONDS),
        )
        logger.warning("BLOCKED %s for %ds — %s (after %d failed attempts)", ip, BLOCK_DURATION_SECONDS, attack_type, FAILED_ATTEMPTS_BEFORE_BLOCK)

    # 6. Alert on high/critical failures
    if severity in ("high", "critical") and not success:
        await db.execute(
            """INSERT INTO alerts (timestamp, alert_type, severity, ip_address, username, message, details)
               VALUES (?, ?, ?, ?, ?, ?, ?)""",
            (
                now, attack_type, severity, ip, body.username,
                f"{attack_type.replace('_',' ').title()} detected from {ip}",
                json.dumps({"reasons": reasons, "risk_score": risk_score}),
            ),
        )

    # 7. Log the attempt
    await db.execute(
        """INSERT INTO login_attempts
           (timestamp, ip_address, username, success, attack_type, severity,
            risk_score, user_agent, blocked, raw_payload)
           VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
        (
            now, ip, body.username, int(success),
            attack_type, severity, risk_score, ua,
            int(should_block),
            json.dumps({"reasons": reasons}),
        ),
    )
    await db.commit()

    logger.info("%s user=%-12s ip=%-15s attack=%-20s sev=%-8s score=%.2f",
                "✅" if success else "❌", body.username, ip,
                attack_type, severity, risk_score)

    return LoginResponse(
        success=success,
        message="Login successful" if success else "Invalid credentials",
        security={
            "ip":          ip,
            "attack_type": attack_type,
            "severity":    severity,
            "risk_score":  round(risk_score, 3),
            "reasons":     reasons,
            "blocked":     should_block,
        },
    )


@router.get("/me")
async def get_me():
    return {"username": "dashboard_user", "role": "analyst"}
