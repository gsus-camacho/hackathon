"""Pydantic schemas for feedback module (ratings)."""
from datetime import datetime, timezone
from typing import Optional
from pydantic import BaseModel, Field, ConfigDict
import uuid


class Rating(BaseModel):
    model_config = ConfigDict(extra="ignore")
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    usuario_identificacion: Optional[str] = None
    identificacion_padre: Optional[str] = None
    nit_colegio: Optional[str] = None
    product_name: Optional[str] = None  # optional: rating for a product
    score: int  # 1..5
    comment: Optional[str] = None
    source: str = "dashboard"  # "whatsapp" | "dashboard"
    created_at: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())


class RatingCreate(BaseModel):
    score: int
    comment: Optional[str] = None
    usuario_identificacion: Optional[str] = None
    identificacion_padre: Optional[str] = None
    nit_colegio: Optional[str] = None
    product_name: Optional[str] = None
    source: str = "dashboard"
