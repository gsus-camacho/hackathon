"""Pydantic schemas for feedback module (thumbs up/down on products)."""
from datetime import datetime, timezone
from typing import Optional, Literal
from pydantic import BaseModel, Field, ConfigDict
import uuid


VoteType = Literal["up", "down"]


class ProductVote(BaseModel):
    model_config = ConfigDict(extra="ignore")
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    product_name: str
    vote: VoteType
    voter_id: Optional[str] = None  # usuario_identificacion or identificacion_padre
    nit_colegio: Optional[str] = None
    source: str = "dashboard"
    created_at: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())


class VoteCreate(BaseModel):
    product_name: str
    vote: VoteType
    voter_id: Optional[str] = None
    nit_colegio: Optional[str] = None
    source: str = "dashboard"


class ProductFeedback(BaseModel):
    """Aggregated per-product feedback."""
    product_name: str
    up: int
    down: int
    total: int
    score_pct: float  # % positive
