"""Pydantic schemas for discounts module (dynamic packages + recharge bundles)."""
from datetime import datetime, timezone
from typing import List, Optional
from pydantic import BaseModel, Field, ConfigDict
import uuid


class PackageItem(BaseModel):
    product_name: str
    quantity: int
    unit_price: float


class Package(BaseModel):
    model_config = ConfigDict(extra="ignore")
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    name: str
    description: str
    items: List[PackageItem]
    original_total: float
    discounted_total: float
    discount_pct: float
    target_segment: str  # e.g. "high_consumption", "low_balance", "general"
    nit_colegio: Optional[str] = None
    valid_until: Optional[str] = None
    created_at: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    active: bool = True


class PackageCreate(BaseModel):
    name: str
    description: str
    items: List[PackageItem]
    discount_pct: float = 10.0
    target_segment: str = "general"
    nit_colegio: Optional[str] = None
    valid_until: Optional[str] = None


class RechargeSuggestion(BaseModel):
    usuario_identificacion: str
    nombre_estudiante: str
    suggested_amount: float
    reason: str
    last_recharge: Optional[str] = None
