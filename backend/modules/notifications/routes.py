"""Notifications + WhatsApp webhook API routes."""
from fastapi import APIRouter, HTTPException, Form
from fastapi.responses import PlainTextResponse
from typing import Optional
from modules.notifications import service as svc
from modules.notifications import repository as repo
from modules.notifications.schemas import SendMessageRequest
from modules.notifications.errors import WhatsAppDeliveryError

router = APIRouter(prefix="/notifications", tags=["notifications"])


@router.get("/")
async def list_notifications(limit: int = 100, kind: Optional[str] = None, read: Optional[bool] = None):
    return await repo.list_notifications(limit, kind, read)


@router.get("/unread-count")
async def unread_count():
    return {"count": await repo.count_unread()}


@router.post("/{notification_id}/read")
async def mark_read(notification_id: str):
    ok = await repo.mark_read(notification_id, True)
    if not ok:
        raise HTTPException(404, "Notificación no encontrada")
    return {"status": "read"}


@router.post("/{notification_id}/unread")
async def mark_unread(notification_id: str):
    ok = await repo.mark_read(notification_id, False)
    if not ok:
        raise HTTPException(404, "Notificación no encontrada")
    return {"status": "unread"}


@router.post("/read-all")
async def read_all():
    modified = await repo.mark_all_read()
    return {"modified": modified}


@router.get("/sessions")
async def list_sessions(limit: int = 50):
    return await svc.list_sessions(limit)


@router.post("/send")
async def send(req: SendMessageRequest):
    try:
        return await svc.send_text(req)
    except WhatsAppDeliveryError as e:
        raise HTTPException(502, f"Twilio error: {e}")


@router.post("/trigger/low-balance")
async def trigger_low_balance(nit_colegio: Optional[str] = None):
    return await svc._send_low_balance_alerts(nit_colegio)


@router.post("/trigger/allergen-check")
async def trigger_allergen_check():
    return await svc._send_allergen_alerts()


@router.post("/trigger/weekly-report")
async def trigger_weekly_report():
    return await svc._send_weekly_nutrition_report()


@router.post("/whatsapp/webhook", response_class=PlainTextResponse)
async def webhook(
    From: str = Form(...),
    Body: str = Form(""),
    ProfileName: Optional[str] = Form(None),
):
    reply = await svc.handle_incoming(From, Body, ProfileName)
    return reply


@router.post("/whatsapp/simulate")
async def simulate(payload: dict):
    phone = payload.get("From", "whatsapp:test")
    body = payload.get("Body", "")
    profile = payload.get("ProfileName")
    reply = await svc.handle_incoming(phone, body, profile)
    return {"reply": reply}
