"""Pydantic schemas for planifications module (weekly meal plan + balance prediction)."""
from datetime import datetime, timezone
from typing import Optional, List
from pydantic import BaseModel, Field, ConfigDict
import uuid


# -- Legacy: balance prediction (kept for at-risk dashboard) --

class BalancePrediction(BaseModel):
    usuario_identificacion: str
    nombre_estudiante: str
    nit_colegio: Optional[str] = None
    current_balance: float
    avg_daily_spend: float
    days_remaining: int
    risk_level: str
    last_recharge_date: Optional[str] = None
    last_consumption_date: Optional[str] = None


class StudentBalance(BaseModel):
    usuario_identificacion: str
    nombre_estudiante: str
    nit_colegio: Optional[str] = None
    total_recargas: float
    total_consumo: float
    current_balance: float
    last_activity: Optional[str] = None


# -- Weekly meal planner --

class MealItem(BaseModel):
    """Single product assignment for a day in the weekly plan."""
    day: int  # 0..6 (Mon..Sun)
    product_name: str
    quantity: int = 1
    unit_price: float


class MealPlan(BaseModel):
    model_config = ConfigDict(extra="ignore")
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    hijo_id: str  # references hijos.id
    usuario_identificacion: Optional[str] = None
    nombre_estudiante: Optional[str] = None
    week_start: str  # ISO date for Monday of the week
    minimum_budget: float = 0.0
    items: List[MealItem] = Field(default_factory=list)
    current_total: float = 0.0
    goal_met: bool = False
    reward: Optional[str] = None
    created_at: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    updated_at: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())


class MealPlanCreate(BaseModel):
    hijo_id: str
    week_start: str
    minimum_budget: float = 50000.0
    items: List[MealItem] = Field(default_factory=list)


class MealItemAdd(BaseModel):
    day: int
    product_name: str
    quantity: int = 1
    unit_price: float
