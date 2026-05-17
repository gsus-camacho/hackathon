"""Pydantic schemas for statistics module (benchmark + satisfaction)."""
from typing import Optional, List
from pydantic import BaseModel


class SchoolStats(BaseModel):
    nit_colegio: str
    colegio: str
    total_students: int
    total_ventas: int
    total_revenue: float
    total_recargas: float
    avg_ticket: float
    satisfaction_score: float  # 1..5
    benchmark_position: Optional[int] = None  # rank among schools
    score: float  # health composite 0..100


class Benchmark(BaseModel):
    metric: str
    school_value: float
    network_avg: float
    network_top: float
    delta_vs_avg_pct: float


class DashboardKpis(BaseModel):
    active_alerts: int
    students_at_risk: int
    package_revenue: float
    satisfaction_score: float
    total_students: int
    total_revenue_30d: float
    total_recargas_30d: float
    bot_sessions_today: int


class TopProduct(BaseModel):
    name: str
    units: int
    revenue: float


class DailySeries(BaseModel):
    date: str
    ventas: float
    recargas: float


class ActivityItem(BaseModel):
    timestamp: str
    kind: str
    title: str
    detail: str
