"""
Alerts Router
=============
GET    /api/alerts           — List alerts (with filters)
PATCH  /api/alerts/{id}/ack  — Acknowledge an alert
PATCH  /api/alerts/{id}/resolve — Resolve an alert
DELETE /api/alerts/{id}      — Delete an alert
"""

from fastapi import APIRouter, Depends, Query, HTTPException
import time
import aiosqlite

from app.core.database import get_db

router = APIRouter()


@router.get("")
async def list_alerts(
    resolved:  str = Query(default="false"),
    severity:  str = Query(default="all"),
    limit:     int = Query(default=100, ge=1, le=500),
    db: aiosqlite.Connection = Depends(get_db),
):
    where_clauses = []
    params = []

    if resolved == "false":
        where_clauses.append("resolved = 0")
    elif resolved == "true":
        where_clauses.append("resolved = 1")

    if severity != "all":
        where_clauses.append("severity = ?")
        params.append(severity)

    where = ("WHERE " + " AND ".join(where_clauses)) if where_clauses else ""

    async with db.execute(
        f"""SELECT id, timestamp, alert_type, severity, ip_address,
                   username, message, details, acknowledged, resolved
            FROM alerts
            {where}
            ORDER BY timestamp DESC
            LIMIT ?""",
        params + [limit],
    ) as cursor:
        rows = await cursor.fetchall()

    return {"alerts": [dict(r) for r in rows], "total": len(rows)}


@router.patch("/{alert_id}/ack")
async def acknowledge_alert(
    alert_id: int,
    db: aiosqlite.Connection = Depends(get_db),
):
    await db.execute(
        "UPDATE alerts SET acknowledged = 1 WHERE id = ?", (alert_id,)
    )
    await db.commit()
    return {"ok": True}


@router.patch("/{alert_id}/resolve")
async def resolve_alert(
    alert_id: int,
    db: aiosqlite.Connection = Depends(get_db),
):
    await db.execute(
        "UPDATE alerts SET resolved = 1, acknowledged = 1 WHERE id = ?", (alert_id,)
    )
    await db.commit()
    return {"ok": True}


@router.delete("/{alert_id}")
async def delete_alert(
    alert_id: int,
    db: aiosqlite.Connection = Depends(get_db),
):
    async with db.execute("SELECT id FROM alerts WHERE id = ?", (alert_id,)) as c:
        if not await c.fetchone():
            raise HTTPException(status_code=404, detail="Alert not found")
    await db.execute("DELETE FROM alerts WHERE id = ?", (alert_id,))
    await db.commit()
    return {"ok": True}
