"""
Logs Router
===========
GET  /api/logs           — Paginated login attempts feed (live dashboard table)
GET  /api/logs/events    — Raw log events from Nginx/app
"""

from fastapi import APIRouter, Depends, Query
import time
import aiosqlite

from app.core.database import get_db

router = APIRouter()


@router.get("")
async def get_login_attempts(
    page:     int  = Query(default=1, ge=1),
    limit:    int  = Query(default=50, ge=1, le=200),
    severity: str  = Query(default="all"),
    attack:   str  = Query(default="all"),
    db: aiosqlite.Connection = Depends(get_db),
):
    offset = (page - 1) * limit
    where_clauses = []
    params = []

    if severity != "all":
        where_clauses.append("severity = ?")
        params.append(severity)
    if attack != "all":
        where_clauses.append("attack_type = ?")
        params.append(attack)

    where = ("WHERE " + " AND ".join(where_clauses)) if where_clauses else ""

    async with db.execute(
        f"""SELECT id, timestamp, ip_address, username, success,
                   attack_type, severity, risk_score, user_agent, blocked
            FROM login_attempts
            {where}
            ORDER BY timestamp DESC
            LIMIT ? OFFSET ?""",
        params + [limit, offset],
    ) as cursor:
        rows = await cursor.fetchall()

    async with db.execute(
        f"SELECT COUNT(*) FROM login_attempts {where}", params
    ) as c:
        total = (await c.fetchone())[0]

    return {
        "attempts": [dict(r) for r in rows],
        "total":    total,
        "page":     page,
        "limit":    limit,
        "pages":    (total + limit - 1) // limit,
    }


@router.get("/events")
async def get_log_events(
    limit: int = Query(default=100, ge=1, le=500),
    db: aiosqlite.Connection = Depends(get_db),
):
    async with db.execute(
        """SELECT id, timestamp, source, ip_address, method, path,
                  status_code, duration_ms, attack_type, severity, risk_score, flagged
           FROM log_events
           ORDER BY timestamp DESC
           LIMIT ?""",
        (limit,),
    ) as cursor:
        rows = await cursor.fetchall()

    return {"events": [dict(r) for r in rows]}
