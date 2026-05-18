"""
Log Monitor Service
===================
Watches Nginx access.log in real-time using tail-like async polling.
Parses each new log line → runs through the AI detector → stores results.

WHY file-based (not socket/syslog)?
  Phase 1: Simplest approach, no infrastructure.
  Phase 2: Replace with Filebeat + Kafka for production.

Nginx Combined Log Format:
  $remote_addr - $remote_user [$time_local] "$request" $status $body_bytes_sent
  "$http_referer" "$http_user_agent" $request_time
"""

import asyncio
import re
import os
import time
import json
import logging
import aiosqlite
from pathlib import Path

from app.core.config import settings
from app.ml.detector import SecurityDetector

logger = logging.getLogger(__name__)

# Nginx combined log format regex
NGINX_LOG_RE = re.compile(
    r'(?P<ip>[\d\.]+) - (?P<user>\S+) \[(?P<time>[^\]]+)\] '
    r'"(?P<method>\w+) (?P<path>\S+) (?P<proto>[^"]+)" '
    r'(?P<status>\d{3}) (?P<size>\d+) '
    r'"(?P<referer>[^"]*)" "(?P<ua>[^"]*)"'
    r'(?: (?P<duration>[\d\.]+))?'
)


def parse_nginx_line(line: str) -> dict | None:
    """Parse one Nginx access log line into a structured dict."""
    m = NGINX_LOG_RE.match(line.strip())
    if not m:
        return None
    return {
        "ip":        m.group("ip"),
        "method":    m.group("method"),
        "path":      m.group("path"),
        "status":    int(m.group("status")),
        "size":      int(m.group("size")),
        "user_agent": m.group("ua"),
        "duration":  float(m.group("duration") or 0),
        "raw":       line.strip(),
    }


class LogMonitor:
    """
    Async background service that tail-follows one or more log files
    and feeds parsed lines into the SecurityDetector.
    """

    def __init__(self, detector: SecurityDetector):
        self.detector = detector
        self._task: asyncio.Task | None = None
        self._running = False

    async def start(self):
        self._running = True
        self._task = asyncio.create_task(self._monitor_loop())
        logger.info("Log monitor started")

    async def stop(self):
        self._running = False
        if self._task:
            self._task.cancel()
            try:
                await self._task
            except asyncio.CancelledError:
                pass

    async def _monitor_loop(self):
        """
        Main loop: tries to tail Nginx log + generates synthetic log events
        when running in local dev (no real Nginx).
        """
        log_path = Path(settings.NGINX_LOG_PATH)

        # In local dev, Nginx may not be running
        if log_path.exists():
            logger.info("Monitoring Nginx log: %s", log_path)
            await asyncio.gather(
                self._tail_file(str(log_path), source="nginx"),
                self._synthetic_traffic_generator(),
            )
        else:
            logger.warning(
                "Nginx log not found at %s — running synthetic traffic generator only",
                log_path,
            )
            await self._synthetic_traffic_generator()

    async def _tail_file(self, path: str, source: str):
        """Async tail -f implementation."""
        with open(path, "r") as f:
            f.seek(0, 2)  # Seek to end
            while self._running:
                line = f.readline()
                if line:
                    await self._process_line(line, source)
                else:
                    await asyncio.sleep(0.5)

    async def _process_line(self, line: str, source: str):
        """Parse, analyze, and store one log line."""
        parsed = parse_nginx_line(line)
        if not parsed:
            return

        result = await self.detector.analyze_log_line(parsed)

        try:
            from app.core.database import DB_PATH
            async with aiosqlite.connect(DB_PATH) as db:
                db.row_factory = aiosqlite.Row
                await db.execute(
                    """INSERT INTO log_events
                       (timestamp, source, ip_address, method, path,
                        status_code, response_size, duration_ms,
                        user_agent, attack_type, severity, risk_score, flagged)
                       VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                    (
                        time.time(), source, parsed["ip"], parsed["method"],
                        parsed["path"], parsed["status"], parsed["size"],
                        parsed["duration"] * 1000,
                        parsed["user_agent"], result.attack_type,
                        result.severity, result.risk_score,
                        int(result.should_block),
                    ),
                )
                await db.commit()
        except Exception as e:
            logger.error("Failed to store log event: %s", e)

    async def _synthetic_traffic_generator(self):
        """
        Generates realistic synthetic log events when no real Nginx log exists.
        Useful for development and demo mode.
        Creates a mix of normal + occasional attack traffic.
        """
        import random

        NORMAL_PATHS  = ["/", "/login", "/dashboard", "/api/health", "/static/main.js"]
        ATTACK_PATHS  = [
            "/admin' OR '1'='1",
            "/../../../etc/passwd",
            "/wp-admin",
            "/phpmyadmin",
            "/.env",
            "/<script>alert(1)</script>",
        ]
        IPS = [f"192.168.1.{i}" for i in range(1, 20)] + ["45.33.32.156", "185.220.101.34"]

        event_count = 0
        while self._running:
            await asyncio.sleep(random.uniform(2, 8))   # random inter-arrival

            is_attack = random.random() < 0.08          # 8% attack rate
            ip     = random.choice(IPS)
            method = "GET" if not is_attack else random.choice(["GET", "POST"])
            path   = random.choice(ATTACK_PATHS if is_attack else NORMAL_PATHS)
            status = 200 if not is_attack else random.choice([400, 403, 404, 500])
            ua     = "Mozilla/5.0" if not is_attack else "sqlmap/1.7 python-requests"

            fake_line = (
                f'{ip} - - [01/Jan/2025:00:00:00 +0000] '
                f'"{method} {path} HTTP/1.1" {status} 1234 "-" "{ua}" 0.05'
            )
            await self._process_line(fake_line, "synthetic")
            event_count += 1

            # Periodically retrain the ML model
            if event_count % 500 == 0:
                await self.detector.retrain()
                logger.info("ML model retrained after %d events", event_count)
