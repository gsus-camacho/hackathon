"""Pydantic schemas for notifications module (WhatsApp alerts + read/unread inbox)."""
from datetime import datetime, timezone
from typing import Optional, Literal
from pydantic import BaseModel, Field, ConfigDict
import uuid


NotificationKind = Literal[
    "allergen_alert",
    "low_balance",
    "no_consumption",
    "daily_report",
    "package_offer",
    "weekly_nutrition",
    "meal_plan_reward",
    "new_plan_product",
    "bot_response",
    "custom",
]


class Notification(BaseModel):
    model_config = ConfigDict(extra="ignore")
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    kind: NotificationKind
    recipient_phone: str
    recipient_name: Optional[str] = None
    usuario_identificacion: Optional[str] = None
    identificacion_padre: Optional[str] = None
    nit_colegio: Optional[str] = None
    message: str
    twilio_sid: Optional[str] = None
    status: str = "pending"
    error: Optional[str] = None
    read: bool = False
    created_at: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    read_at: Optional[str] = None


class SendMessageRequest(BaseModel):
    to: str
    body: str
    kind: NotificationKind = "custom"
    recipient_name: Optional[str] = None
    usuario_identificacion: Optional[str] = None
    identificacion_padre: Optional[str] = None


class IncomingMessage(BaseModel):
    From: str
    Body: str
    ProfileName: Optional[str] = None
    WaId: Optional[str] = None


class BotSession(BaseModel):
    model_config = ConfigDict(extra="ignore")
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    phone: str
    identificacion_padre: Optional[str] = None
    last_intent: Optional[str] = None
    messages: list = Field(default_factory=list)
    created_at: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    updated_at: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
