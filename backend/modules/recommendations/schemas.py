"""Pydantic schemas for recommendations module (Gemini-powered)."""
from datetime import datetime, timezone
from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field, ConfigDict
import uuid


class Recommendation(BaseModel):
    model_config = ConfigDict(extra="ignore")
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    nit_colegio: Optional[str] = None
    usuario_identificacion: Optional[str] = None
    kind: str  # "product" | "package" | "nutrition" | "operational"
    title: str
    summary: str
    rationale: str
    impact_score: float  # 0..100
    data: Dict[str, Any] = Field(default_factory=dict)
    created_at: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())


class RecommendationRequest(BaseModel):
    nit_colegio: Optional[str] = None
    focus: str = "general"  # "revenue" | "nutrition" | "safety" | "general"


class Allergen(BaseModel):
    model_config = ConfigDict(extra="ignore")
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    usuario_identificacion: str
    nombre_estudiante: Optional[str] = None
    identificacion_padre: Optional[str] = None
    nit_colegio: Optional[str] = None
    allergens: List[str]  # e.g. ["mani", "lactosa"]
    notes: Optional[str] = None
    created_at: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())


class AllergenCreate(BaseModel):
    usuario_identificacion: str
    nombre_estudiante: Optional[str] = None
    identificacion_padre: Optional[str] = None
    nit_colegio: Optional[str] = None
    allergens: List[str]
    notes: Optional[str] = None
