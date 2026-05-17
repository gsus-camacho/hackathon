"""Notifications API routes - Automated notification triggers and management."""
import logging
from typing import Optional, Dict, List
from fastapi import APIRouter, HTTPException, BackgroundTasks
from pydantic import BaseModel, Field

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/notifications", tags=["notifications"])


@router.post("/trigger/allergen-check")
async def trigger_allergen_check(background_tasks: BackgroundTasks):
    """
    Manually trigger allergen alert check.
    Scans recent transactions for allergen matches.
    """
    from backend.services.notification_service import get_notification_service
    
    service = get_notification_service()
    alerts = await service.check_allergen_alerts()
    
    return {
        "check_type": "allergen",
        "alerts_sent": len(alerts),
        "details": alerts
    }


@router.post("/trigger/low-balance-check")
async def trigger_low_balance_check(background_tasks: BackgroundTasks):
    """
    Manually trigger low balance check.
    Scans for students with critically low balance.
    """
    from backend.services.notification_service import get_notification_service
    
    service = get_notification_service()
    alerts = await service.check_low_balance()
    
    return {
        "check_type": "low_balance",
        "alerts_sent": len(alerts),
        "details": alerts
    }


@router.post("/trigger/no-consumption-check")
async def trigger_no_consumption_check(background_tasks: BackgroundTasks):
    """
    Manually trigger no consumption check.
    Sends alerts for students who haven't purchased anything today.
    """
    from backend.services.notification_service import get_notification_service
    
    service = get_notification_service()
    alerts = await service.check_no_consumption()
    
    return {
        "check_type": "no_consumption",
        "alerts_sent": len(alerts),
        "details": alerts
    }


@router.post("/trigger/weekly-report")
async def trigger_weekly_report(background_tasks: BackgroundTasks):
    """
    Manually trigger weekly nutrition report.
    Sends summary reports to all parents.
    """
    from backend.services.notification_service import get_notification_service
    
    service = get_notification_service()
    reports = await service.send_weekly_nutrition_report()
    
    return {
        "check_type": "weekly_report",
        "reports_sent": len(reports),
        "details": reports
    }


@router.post("/trigger/all")
async def trigger_all_notifications(background_tasks: BackgroundTasks):
    """
    Trigger all notification checks at once.
    Useful for testing or manual runs.
    """
    from backend.services.notification_service import get_notification_service
    
    service = get_notification_service()
    
    results = {}
    
    # Run all checks
    results["allergen"] = await service.check_allergen_alerts()
    results["low_balance"] = await service.check_low_balance()
    results["no_consumption"] = await service.check_no_consumption()
    
    return {
        "summary": {
            "allergen_alerts": len(results["allergen"]),
            "low_balance_alerts": len(results["low_balance"]),
            "no_consumption_alerts": len(results["no_consumption"]),
        },
        "details": results
    }


@router.get("/stats")
async def get_notification_stats(
    days: int = 7,
    kind: Optional[str] = None
):
    """
    Get notification statistics.
    """
    from core.postgres import fetch_all, fetch_one
    
    try:
        # Total notifications
        total_query = """
            SELECT COUNT(*) as total
            FROM notifications
            WHERE timestamp >= NOW() - INTERVAL '{days} days'
        """.format(days=days)
        
        if kind:
            total_query += " AND kind = '{kind}'".format(kind=kind)
        
        total_result = await fetch_one(total_query)
        total = total_result["total"] if total_result else 0
        
        # By status
        status_query = """
            SELECT status, COUNT(*) as count
            FROM notifications
            WHERE timestamp >= NOW() - INTERVAL '{days} days'
        """.format(days=days)
        
        if kind:
            status_query += " AND kind = '{kind}'".format(kind=kind)
        
        status_query += " GROUP BY status"
        
        status_results = await fetch_all(status_query)
        status_breakdown = {r["status"]: r["count"] for r in status_results}
        
        # By kind
        kind_query = """
            SELECT kind, COUNT(*) as count
            FROM notifications
            WHERE timestamp >= NOW() - INTERVAL '{days} days'
            GROUP BY kind
            ORDER BY count DESC
        """
        kind_results = await fetch_all(kind_query)
        kind_breakdown = {r["kind"]: r["count"] for r in kind_results}
        
        # Recent notifications
        recent_query = """
            SELECT kind, status, timestamp, recipient_phone
            FROM notifications
            WHERE timestamp >= NOW() - INTERVAL '{days} days'
            ORDER BY timestamp DESC
            LIMIT 20
        """.format(days=days)
        
        recent_results = await fetch_all(recent_query)
        recent = [dict(r) for r in recent_results]
        
        return {
            "period_days": days,
            "total_notifications": total,
            "status_breakdown": status_breakdown,
            "kind_breakdown": kind_breakdown,
            "recent_notifications": recent
        }
        
    except Exception as e:
        logger.error(f"Error getting notification stats: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/recent")
async def get_recent_notifications(limit: int = 50, kind: Optional[str] = None):
    """
    Get recent notifications.
    """
    from modules.notifications import service as notif_svc
    
    # Use existing notification service
    notifications = await notif_svc.list_recent(limit)
    
    if kind:
        notifications = [n for n in notifications if n.get("kind") == kind]
    
    return {
        "notifications": notifications,
        "count": len(notifications)
    }


@router.get("/sessions")
async def get_bot_sessions(limit: int = 50):
    """
    Get recent bot conversation sessions.
    """
    from backend.services.conversation_memory import get_conversation_memory
    
    memory = get_conversation_memory()
    sessions = await memory.get_recent_sessions(limit)
    
    return {
        "sessions": sessions,
        "count": len(sessions)
    }


@router.post("/cleanup/sessions")
async def cleanup_expired_sessions():
    """
    Clean up expired bot sessions.
    """
    from backend.services.conversation_memory import get_conversation_memory
    
    memory = get_conversation_memory()
    deleted = await memory.cleanup_expired_sessions()
    
    return {
        "deleted_sessions": deleted
    }