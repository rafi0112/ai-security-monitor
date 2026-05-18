"""
Stats Router
============
GET /api/stats/overview    — Summary numbers for the dashboard header
GET /api/stats/timeline    — Time-series data for the charts
GET /api/stats/top-ips     — Most active/suspicious IPs
GET /api/stats/attack-dist — Attack type distribution
"""

from fastapi import APIRouter, Depends, Query
import time
import logging
import aiosqlite

from app.core.database import get_db

logger = logging.getLogger(__name__)
router = APIRouter()


@router.get("/overview")
async def get_overview(db: aiosqlite.Connection = Depends(get_db)):
    """
    Key numbers shown in dashboard header cards.
    Time windows: last 24 hours.
    """
    since = time.time() - 86400  # 24 hours ago

    # Total attempts
    async with db.execute(
        "SELECT COUNT(*) FROM login_attempts WHERE timestamp > ?", (since,)
    ) as c:
        total = (await c.fetchone())[0]

    # Successful logins
    async with db.execute(
        "SELECT COUNT(*) FROM login_attempts WHERE timestamp > ? AND success = 1", (since,)
    ) as c:
        success = (await c.fetchone())[0]

    # Failed logins
    async with db.execute(
        "SELECT COUNT(*) FROM login_attempts WHERE timestamp > ? AND success = 0", (since,)
    ) as c:
        failed = (await c.fetchone())[0]

    # Attacks detected
    async with db.execute(
        "SELECT COUNT(*) FROM login_attempts WHERE timestamp > ? AND attack_type != 'none'", (since,)
    ) as c:
        attacks = (await c.fetchone())[0]

    # Active alerts (unresolved)
    async with db.execute(
        "SELECT COUNT(*) FROM alerts WHERE resolved = 0"
    ) as c:
        active_alerts = (await c.fetchone())[0]

    # Critical alerts in last hour
    async with db.execute(
        "SELECT COUNT(*) FROM alerts WHERE timestamp > ? AND severity = 'critical'",
        (time.time() - 3600,),
    ) as c:
        critical_alerts = (await c.fetchone())[0]

    # Blocked IPs
    async with db.execute(
        "SELECT COUNT(*) FROM blocked_ips WHERE (expires_at IS NULL OR expires_at > ?)",
        (time.time(),),
    ) as c:
        blocked_ips = (await c.fetchone())[0]

    # Unique IPs in last 24h
    async with db.execute(
        "SELECT COUNT(DISTINCT ip_address) FROM login_attempts WHERE timestamp > ?", (since,)
    ) as c:
        unique_ips = (await c.fetchone())[0]

    # Average risk score
    async with db.execute(
        "SELECT AVG(risk_score) FROM login_attempts WHERE timestamp > ?", (since,)
    ) as c:
        row = await c.fetchone()
        avg_risk = round(row[0] or 0.0, 3)

    return {
        "total_attempts":  total,
        "successful":      success,
        "failed":          failed,
        "attacks":         attacks,
        "active_alerts":   active_alerts,
        "critical_alerts": critical_alerts,
        "blocked_ips":     blocked_ips,
        "unique_ips":      unique_ips,
        "avg_risk_score":  avg_risk,
        "success_rate":    round(success / total * 100, 1) if total else 0,
        "attack_rate":     round(attacks / total * 100, 1) if total else 0,
    }


@router.get("/timeline")
async def get_timeline(
    hours: int = Query(default=24, ge=1, le=168),
    db: aiosqlite.Connection = Depends(get_db),
):
    """
    Bucketed time-series for line/bar charts.
    Returns one data point per hour for the last N hours.
    """
    now  = time.time()
    since = now - hours * 3600

    # Get all attempts in range
    async with db.execute(
        """SELECT timestamp, success, attack_type, severity, risk_score
           FROM login_attempts WHERE timestamp > ? ORDER BY timestamp""",
        (since,),
    ) as cursor:
        rows = await cursor.fetchall()

    # Build hourly buckets
    buckets: dict[int, dict] = {}
    for hour_offset in range(hours):
        bucket_ts = int((now - (hours - 1 - hour_offset) * 3600) // 3600) * 3600
        buckets[bucket_ts] = {
            "timestamp": bucket_ts * 1000,  # ms for JS
            "total": 0, "success": 0, "failed": 0,
            "attacks": 0, "critical": 0,
        }

    for row in rows:
        bucket_key = int(row["timestamp"] // 3600) * 3600
        if bucket_key in buckets:
            b = buckets[bucket_key]
            b["total"] += 1
            if row["success"]:
                b["success"] += 1
            else:
                b["failed"] += 1
            if row["attack_type"] not in ("none", None):
                b["attacks"] += 1
            if row["severity"] == "critical":
                b["critical"] += 1

    return {"timeline": list(buckets.values()), "hours": hours}


@router.get("/top-ips")
async def get_top_ips(
    limit: int = Query(default=10, ge=1, le=50),
    db: aiosqlite.Connection = Depends(get_db),
):
    """Top IPs by attempt count in last 24h with threat metadata."""
    since = time.time() - 86400

    async with db.execute(
        """SELECT
            ip_address,
            COUNT(*) as total,
            SUM(CASE WHEN success=0 THEN 1 ELSE 0 END) as failures,
            SUM(CASE WHEN attack_type != 'none' THEN 1 ELSE 0 END) as attacks,
            MAX(risk_score) as max_risk,
            MAX(severity) as max_severity,
            GROUP_CONCAT(DISTINCT attack_type) as attack_types
           FROM login_attempts
           WHERE timestamp > ?
           GROUP BY ip_address
           ORDER BY total DESC
           LIMIT ?""",
        (since, limit),
    ) as cursor:
        rows = await cursor.fetchall()

    result = []
    for row in rows:
        is_blocked = False
        async with db.execute(
            "SELECT ip FROM blocked_ips WHERE ip = ? AND (expires_at IS NULL OR expires_at > ?)",
            (row["ip_address"], time.time()),
        ) as c:
            is_blocked = (await c.fetchone()) is not None

        result.append({
            "ip":           row["ip_address"],
            "total":        row["total"],
            "failures":     row["failures"],
            "attacks":      row["attacks"],
            "max_risk":     round(row["max_risk"] or 0, 3),
            "max_severity": row["max_severity"] or "low",
            "attack_types": [a for a in (row["attack_types"] or "").split(",") if a and a != "none"],
            "blocked":      is_blocked,
        })

    return {"top_ips": result}


@router.get("/attack-distribution")
async def get_attack_distribution(
    hours: int = Query(default=24),
    db: aiosqlite.Connection = Depends(get_db),
):
    """Attack type counts for pie/donut chart."""
    since = time.time() - hours * 3600

    async with db.execute(
        """SELECT attack_type, severity, COUNT(*) as count
           FROM login_attempts
           WHERE timestamp > ? AND attack_type != 'none'
           GROUP BY attack_type, severity
           ORDER BY count DESC""",
        (since,),
    ) as cursor:
        rows = await cursor.fetchall()

    COLORS = {
        "brute_force":         "#ef4444",
        "sqli":                "#f97316",
        "xss":                 "#eab308",
        "cmd_injection":       "#dc2626",
        "path_traversal":      "#a855f7",
        "anomaly":             "#06b6d4",
        "ddos":                "#ec4899",
        "credential_stuffing": "#84cc16",
        "scanner":             "#f59e0b",
    }

    return {
        "distribution": [
            {
                "attack_type": row["attack_type"],
                "severity":    row["severity"],
                "count":       row["count"],
                "color":       COLORS.get(row["attack_type"], "#6b7280"),
            }
            for row in rows
        ]
    }
