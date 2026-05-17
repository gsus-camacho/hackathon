"""Pydantic schemas for planifications module (balance prediction)."""
from typing import Optional, List
from pydantic import BaseModel


class BalancePrediction(BaseModel):
    usuario_identificacion: str
    nombre_estudiante: str
    nit_colegio: Optional[str] = None
    current_balance: float
    avg_daily_spend: float
    days_remaining: int
    risk_level: str  # "high" | "medium" | "low"
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


class WeeklyPlan(BaseModel):
    nit_colegio: str
    expected_revenue: float
    students_at_risk: int
    students_total: int
    top_products: List[dict]
