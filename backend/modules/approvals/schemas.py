"""Product approval queue — parent allow/block + Gemini fallback."""
from datetime import datetime, timezone
from typing import Optional, List, Literal
from pydantic import BaseModel, Field, ConfigDict
import uuid

ApprovalStatus = Literal["pending", "allowed", "blocked", "auto_blocked", "auto_allowed"]
ApprovalSource = Literal["meal_plan", "catalog_new"]


class ProductApproval(BaseModel):
    model_config = ConfigDict(extra="ignore")
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    hijo_id: str
    usuario_identificacion: str
    nombre_estudiante: str = ""
    identificacion_padre: Optional[str] = None
    parent_phone: Optional[str] = None
    nit_colegio: Optional[str] = None
    product_name: str
    unit_price: float = 0
    source: ApprovalSource = "meal_plan"
    plan_id: Optional[str] = None
    plan_item_index: Optional[int] = None
    status: ApprovalStatus = "pending"
    gemini_risk_level: Optional[str] = None
    gemini_reason: Optional[str] = None
    created_at: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    expires_at: Optional[str] = None
    resolved_at: Optional[str] = None


class ApprovalResolve(BaseModel):
    decision: Literal["allow", "block"]


class CatalogProductCreate(BaseModel):
    product_name: str
    nit_colegio: str
    colegio: Optional[str] = None
    unit_price: float = 0
    category: Optional[str] = None
