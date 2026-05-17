"""Notifications + WhatsApp webhook API routes."""
from fastapi import APIRouter, HTTPException, Request, Form
from fastapi.responses import PlainTextResponse
from typing import Optional
from modules.notifications import service as svc
from modules.notifications.schemas import SendMessageRequest
from modules.notifications.errors import WhatsAppDeliveryError

router = APIRouter(prefix="/notifications", tags=["notifications"])


@router.get("/")
async def list_notifications(limit: int = 50):
    return await svc.list_recent(limit)


@router.get("/sessions")
async def list_sessions(limit: int = 50):
    return await svc.list_sessions(limit)


@router.post("/send")
async def send(req: SendMessageRequest):
    try:
        return await svc.send_text(req)
    except WhatsAppDeliveryError as e:
        raise HTTPException(502, f"Twilio error: {e}")


@router.post("/whatsapp/webhook", response_class=PlainTextResponse)
async def webhook(
    From: str = Form(...),
    Body: str = Form(""),
    ProfileName: Optional[str] = Form(None),
):
    """Twilio inbound message webhook. Returns plain text (Twilio expects 200)."""
    reply = await svc.handle_incoming(From, Body, ProfileName)
    return reply


@router.post("/whatsapp/simulate")
async def simulate(payload: dict):
    """For testing without Twilio inbound — same as webhook but JSON."""
    phone = payload.get("From", "whatsapp:test")
    body = payload.get("Body", "")
    profile = payload.get("ProfileName")
    reply = await svc.handle_incoming(phone, body, profile)
    return {"reply": reply}


@router.post("/test/low-balance")
async def test_low_balance(payload: dict):
    """Quick endpoint to test outbound low balance alert."""
    return await svc.send_low_balance_alert(
        phone=payload.get("phone"),
        name=payload.get("name", "Acudiente"),
        balance=float(payload.get("balance", 0)),
        days=int(payload.get("days", 0)),
    )
