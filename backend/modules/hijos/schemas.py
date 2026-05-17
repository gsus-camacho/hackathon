"""Pydantic schemas for the hijos module (configured children profiles)."""
from datetime import datetime, timezone
from typing import List, Optional
from pydantic import BaseModel, Field, ConfigDict
import uuid


class Hijo(BaseModel):
    model_config = ConfigDict(extra="ignore")
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    usuario_identificacion: str
    nombre_estudiante: str
    identificacion_padre: Optional[str] = None
    nombre_padre: Optional[str] = None
    nit_colegio: Optional[str] = None
    colegio: Optional[str] = None
    grado: Optional[str] = None
    photo_url: Optional[str] = None
    allergens: List[str] = Field(default_factory=list)
    notes: str = ""
    parent_phone: Optional[str] = None  # WhatsApp number for alerts
    created_at: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    updated_at: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())


class HijoCreate(BaseModel):
    usuario_identificacion: str
    nombre_estudiante: Optional[str] = None
    identificacion_padre: Optional[str] = None
    nombre_padre: Optional[str] = None
    nit_colegio: Optional[str] = None
    colegio: Optional[str] = None
    grado: Optional[str] = None
    photo_url: Optional[str] = None
    allergens: List[str] = Field(default_factory=list)
    notes: str = ""
    parent_phone: Optional[str] = None


class HijoUpdate(BaseModel):
    nombre_estudiante: Optional[str] = None
    grado: Optional[str] = None
    photo_url: Optional[str] = None
    allergens: Optional[List[str]] = None
    notes: Optional[str] = None
    parent_phone: Optional[str] = None
