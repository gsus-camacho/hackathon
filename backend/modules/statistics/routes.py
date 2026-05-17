"""Statistics API routes."""
from fastapi import APIRouter, Query
from typing import Optional
from modules.statistics import service as svc

router = APIRouter(prefix="/statistics", tags=["statistics"])


@router.get("/kpis")
async def get_kpis(nit_colegio: Optional[str] = None):
    return await svc.dashboard_kpis(nit_colegio)


@router.get("/series")
async def get_series(nit_colegio: Optional[str] = None, days: int = 14):
    return await svc.daily_series(nit_colegio, days)


@router.get("/top-products")
async def get_top_products(nit_colegio: Optional[str] = None, limit: int = 8):
    return await svc.top_products(nit_colegio, limit)


@router.get("/activity")
async def get_activity(nit_colegio: Optional[str] = None, limit: int = 12):
    return await svc.recent_activity(nit_colegio, limit)


@router.get("/schools")
async def list_schools(limit: int = 50):
    return await svc.list_schools(limit)


@router.get("/benchmark")
async def get_benchmark(nit_colegio: str = Query(...)):
    return await svc.benchmark_school(nit_colegio)


@router.get("/score")
async def get_score(nit_colegio: str = Query(...)):
    score = await svc.school_score(nit_colegio)
    return {"nit_colegio": nit_colegio, "score": score}
