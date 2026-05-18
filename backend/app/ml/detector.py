"""
AI/ML Security Detector
=======================
PHASE 1  ── Rule-based detection (instant, no training needed)
PHASE 2  ── IsolationForest anomaly detection (unsupervised, no labels needed)

WHY IsolationForest?
  • Unsupervised: works WITHOUT labeled attack data
  • Fast: O(n log n) training, O(log n) inference
  • Effective: designed for rare-event anomaly detection
  • Free: scikit-learn, no GPU needed

Feature vector for each login event:
  [hour_of_day, failures_last_60s, unique_ips_last_5min,
   is_known_bad_user, has_sqli_pattern, has_xss_pattern,
   request_rate_last_60s, payload_length]
"""

import re
import time
import asyncio
import logging
from collections import defaultdict, deque
from dataclasses import dataclass, field
from typing import Optional

import numpy as np
from sklearn.ensemble import IsolationForest
from sklearn.preprocessing import StandardScaler

logger = logging.getLogger(__name__)


# ─── KNOWN ATTACK PATTERNS ────────────────────────────────────────────────────
SQLI_PATTERNS = re.compile(
    r"('|--|;|\/\*|\*\/|xp_|UNION|SELECT|INSERT|UPDATE|DELETE|DROP|"
    r"OR\s+1=1|AND\s+1=1|SLEEP\(|BENCHMARK\(|LOAD_FILE|INTO\s+OUTFILE)",
    re.IGNORECASE,
)

XSS_PATTERNS = re.compile(
    r"(<script|<\/script>|javascript:|on\w+\s*=|alert\(|document\.cookie|"
    r"<iframe|<img[^>]+src\s*=|eval\(|String\.fromCharCode)",
    re.IGNORECASE,
)

CMD_INJECTION = re.compile(
    r"(;|\|{1,2}|&&|\$\(|`|\.\./|\/etc\/passwd|\/etc\/shadow|"
    r"\bwhoami\b|\bcurl\b.*http|\bwget\b)",
    re.IGNORECASE,
)

PATH_TRAVERSAL = re.compile(
    r"(\.\./|\.\.\\|%2e%2e|%252e%252e|\/etc\/|\/proc\/|\/sys\/)",
    re.IGNORECASE,
)

# Common credential-stuffing usernames
SUSPICIOUS_USERNAMES = {
    "admin", "root", "administrator", "sa", "postgres", "oracle",
    "test", "guest", "user", "demo", "master", "superuser",
    "backup", "sys", "mysql", "ftpuser", "ubuntu", "pi",
}

# ─── DATA CLASSES ─────────────────────────────────────────────────────────────
@dataclass
class DetectionResult:
    attack_type: str       # none | brute_force | sqli | xss | cmd_injection | path_traversal | anomaly | ddos
    severity: str          # low | medium | high | critical
    risk_score: float      # 0.0 – 1.0
    reasons: list[str] = field(default_factory=list)
    should_block: bool = False


@dataclass
class LoginEvent:
    ip_address: str
    username: str
    success: bool
    user_agent: str = ""
    password_hint: str = ""    # We never store real passwords — only check for patterns
    timestamp: float = field(default_factory=time.time)


# ─── IN-MEMORY SLIDING WINDOW TRACKER ────────────────────────────────────────
class SlidingWindowTracker:
    """
    Tracks events in a time window without a database.
    Used for brute-force and rate-limit detection.

    Structure: {key -> deque of timestamps}
    """
    def __init__(self, window_seconds: int = 60):
        self.window = window_seconds
        self._data: dict[str, deque] = defaultdict(deque)

    def record(self, key: str) -> int:
        """Record an event and return count within the window."""
        now = time.time()
        q = self._data[key]
        q.append(now)
        # Evict events outside the window
        while q and q[0] < now - self.window:
            q.popleft()
        return len(q)

    def count(self, key: str) -> int:
        """Return current count for key within window."""
        now = time.time()
        q = self._data[key]
        while q and q[0] < now - self.window:
            q.popleft()
        return len(q)

    def unique_keys_with_prefix(self, prefix: str) -> int:
        """Count unique sub-keys. E.g. unique IPs for a username."""
        return sum(1 for k in self._data if k.startswith(prefix) and self.count(k) > 0)


# ─── SECURITY DETECTOR ────────────────────────────────────────────────────────
class SecurityDetector:
    """
    Two-layer detector:
    Layer 1 — Rule-based (instant, deterministic, zero training)
    Layer 2 — ML anomaly detection (IsolationForest, retrained periodically)
    """

    def __init__(self):
        # Brute-force trackers
        self.failure_tracker  = SlidingWindowTracker(window_seconds=60)
        self.request_tracker  = SlidingWindowTracker(window_seconds=60)
        self.success_tracker  = SlidingWindowTracker(window_seconds=300)

        # ML model
        self.model   : Optional[IsolationForest] = None
        self.scaler  : Optional[StandardScaler]  = None
        self.trained : bool = False

        # Training data buffer (ring buffer of feature vectors)
        self._training_buffer: deque = deque(maxlen=10_000)

    # ── TRAINING ──────────────────────────────────────────────────────────────
    async def train_initial_model(self):
        """
        Bootstrap with synthetic 'normal' data.
        In production, replace with real historical benign logs.
        """
        logger.info("Training IsolationForest on synthetic baseline data...")

        rng = np.random.default_rng(42)
        n_normal = 500

        # Simulate normal login traffic features
        normal_data = np.column_stack([
            rng.integers(8, 22, n_normal),       # hour_of_day: business hours
            rng.integers(0, 2,  n_normal),        # failures_last_60s: rarely fails
            rng.integers(1, 3,  n_normal),        # unique_ips_last_5min
            np.zeros(n_normal),                   # is_known_bad_user: no
            np.zeros(n_normal),                   # has_sqli_pattern: no
            np.zeros(n_normal),                   # has_xss_pattern: no
            rng.integers(1, 10, n_normal),        # request_rate_60s: low
            rng.integers(5, 30, n_normal),        # payload_length: normal
        ]).astype(float)

        self._training_buffer.extend(normal_data.tolist())
        await self._fit_model()

    async def _fit_model(self):
        """Fit / refit IsolationForest on the buffer."""
        if len(self._training_buffer) < 50:
            return

        X = np.array(list(self._training_buffer))
        self.scaler = StandardScaler()
        X_scaled = self.scaler.fit_transform(X)

        self.model = IsolationForest(
            n_estimators=100,
            contamination=0.05,    # expect ~5% anomalies
            random_state=42,
            n_jobs=-1,
        )
        self.model.fit(X_scaled)
        self.trained = True
        logger.info("✅ IsolationForest retrained on %d samples", len(self._training_buffer))

    async def retrain(self):
        """Periodically called to retrain with accumulated real data."""
        await self._fit_model()

    # ── FEATURE EXTRACTION ────────────────────────────────────────────────────
    def _extract_features(self, event: LoginEvent) -> np.ndarray:
        from datetime import datetime
        dt = datetime.fromtimestamp(event.timestamp)

        features = [
            float(dt.hour),
            float(self.failure_tracker.count(event.ip_address)),
            float(self.request_tracker.count(event.username)),
            float(event.username.lower() in SUSPICIOUS_USERNAMES),
            float(bool(SQLI_PATTERNS.search(event.username) or
                       SQLI_PATTERNS.search(event.password_hint))),
            float(bool(XSS_PATTERNS.search(event.username) or
                       XSS_PATTERNS.search(event.password_hint))),
            float(self.request_tracker.count(event.ip_address)),
            float(len(event.username) + len(event.password_hint)),
        ]
        return np.array(features, dtype=float)

    # ── ANOMALY SCORE ─────────────────────────────────────────────────────────
    def _get_anomaly_score(self, features: np.ndarray) -> float:
        """
        IsolationForest score_samples returns values in range [-0.5, 0.5].
        We normalise to [0, 1] where 1 = most anomalous.
        """
        if not self.trained or self.model is None:
            return 0.0

        X = features.reshape(1, -1)
        X_scaled = self.scaler.transform(X)
        raw = self.model.score_samples(X_scaled)[0]
        # raw: more negative = more anomalous
        # Map [-0.5, 0] → [1, 0]  (invert and clip)
        score = float(np.clip(-raw * 2, 0, 1))
        return score

    # ── RULE-BASED LAYER ──────────────────────────────────────────────────────
    def _rule_based_detect(self, event: LoginEvent) -> DetectionResult:
        reasons = []
        attack_type = "none"
        severity = "low"
        risk_score = 0.0
        should_block = False

        text_to_check = f"{event.username} {event.password_hint} {event.user_agent}"

        # 1. SQL Injection
        if SQLI_PATTERNS.search(text_to_check):
            attack_type = "sqli"
            severity = "critical"
            risk_score = 0.95
            should_block = True
            reasons.append("SQL injection pattern in credentials")

        # 2. XSS
        elif XSS_PATTERNS.search(text_to_check):
            attack_type = "xss"
            severity = "high"
            risk_score = 0.85
            should_block = True
            reasons.append("XSS payload detected in input")

        # 3. Command Injection
        elif CMD_INJECTION.search(text_to_check):
            attack_type = "cmd_injection"
            severity = "critical"
            risk_score = 0.95
            should_block = True
            reasons.append("Command injection pattern detected")

        # 4. Path Traversal
        elif PATH_TRAVERSAL.search(text_to_check):
            attack_type = "path_traversal"
            severity = "high"
            risk_score = 0.80
            should_block = True
            reasons.append("Path traversal attempt detected")

        # 5. Brute Force
        if not event.success:
            fail_count = self.failure_tracker.record(event.ip_address)
            if fail_count >= 10:
                attack_type = "brute_force"
                severity = "critical"
                risk_score = max(risk_score, 0.90)
                should_block = True
                reasons.append(f"Brute force: {fail_count} failures in 60s from {event.ip_address}")
            elif fail_count >= 5:
                attack_type = "brute_force" if attack_type == "none" else attack_type
                severity = "high" if severity in ("low", "medium") else severity
                risk_score = max(risk_score, 0.70)
                reasons.append(f"Multiple failures: {fail_count} in 60s")
            elif fail_count >= 3:
                risk_score = max(risk_score, 0.40)
                reasons.append(f"Repeated failures: {fail_count}")

        # 6. Suspicious username
        if event.username.lower() in SUSPICIOUS_USERNAMES:
            risk_score = max(risk_score, 0.30)
            reasons.append(f"Known-targeted username: {event.username}")
            if attack_type == "none":
                attack_type = "credential_stuffing"
                severity = "medium"

        # 7. High request rate (DDoS-like)
        req_count = self.request_tracker.record(event.ip_address)
        if req_count > 30:
            risk_score = max(risk_score, 0.75)
            attack_type = "ddos" if attack_type == "none" else attack_type
            severity = "high"
            should_block = True
            reasons.append(f"High request rate: {req_count} req/60s")

        return DetectionResult(
            attack_type=attack_type,
            severity=severity,
            risk_score=risk_score,
            reasons=reasons,
            should_block=should_block,
        )

    # ── MAIN DETECTION ENTRY POINT ────────────────────────────────────────────
    async def analyze_login(self, event: LoginEvent) -> DetectionResult:
        """
        Full two-layer analysis:
        1. Rule-based (always runs)
        2. ML anomaly score (merged into risk_score)
        """
        # Layer 1: rules
        result = self._rule_based_detect(event)

        # Layer 2: ML
        features = self._extract_features(event)
        anomaly_score = self._get_anomaly_score(features)

        # Merge scores (take max, but let ML catch things rules miss)
        if anomaly_score > 0.6 and result.attack_type == "none":
            result.attack_type = "anomaly"
            result.severity = "medium" if anomaly_score < 0.8 else "high"
            result.reasons.append(f"ML anomaly score: {anomaly_score:.2f}")

        result.risk_score = max(result.risk_score, anomaly_score * 0.5)

        # Feed to training buffer (only benign-looking events)
        if result.risk_score < 0.3:
            self._training_buffer.append(features.tolist())

        return result

    async def analyze_log_line(self, line: dict) -> DetectionResult:
        """Analyze a parsed Nginx/app log line."""
        reasons = []
        attack_type = "none"
        severity = "low"
        risk_score = 0.0
        should_block = False

        path = line.get("path", "")
        ua   = line.get("user_agent", "")
        ip   = line.get("ip", "")
        status = line.get("status", 200)

        text = f"{path} {ua}"

        if SQLI_PATTERNS.search(text):
            attack_type, severity, risk_score, should_block = "sqli", "critical", 0.95, True
            reasons.append("SQLi in URL/UA")
        elif XSS_PATTERNS.search(text):
            attack_type, severity, risk_score, should_block = "xss", "high", 0.85, True
            reasons.append("XSS in URL/UA")
        elif PATH_TRAVERSAL.search(text):
            attack_type, severity, risk_score, should_block = "path_traversal", "high", 0.80, True
            reasons.append("Path traversal in URL")

        # 404 storm
        if status == 404:
            rate = self.request_tracker.record(f"404:{ip}")
            if rate > 20:
                attack_type = "scanner"
                severity = "medium"
                risk_score = max(risk_score, 0.6)
                reasons.append(f"404 scanning: {rate} not-found in 60s")

        return DetectionResult(
            attack_type=attack_type,
            severity=severity,
            risk_score=risk_score,
            reasons=reasons,
            should_block=should_block,
        )
