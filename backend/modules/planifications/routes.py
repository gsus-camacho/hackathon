"""Planifications API routes."""
from fastapi import APIRouter, HTTPException
from typing import Optional
from modules.planifications import service as svc
from modules.planifications.schemas import MealPlanCreate, MealItemAdd
from modules.planifications.errors import PlanificationsError

router = APIRouter(prefix="/planifications", tags=["planifications"])


# -- Balance --

@router.get("/balance/{usuario_identificacion}")
async def balance(usuario_identificacion: str):
    pred = await svc.predict_balance(usuario_identificacion)
    if not pred:
        raise HTTPException(404, "Estudiante no encontrado")
    return pred


@router.get("/at-risk")
async def at_risk(nit_colegio: Optional[str] = None, limit: int = 50):
    return await svc.students_at_risk(nit_colegio, limit)


@router.get("/students/search")
async def search(q: str, limit: int = 20):
    return await svc.search_students(q, limit)


# -- Meal plans --

@router.post("/plans")
async def create_plan(req: MealPlanCreate):
    return await svc.create_plan(req)


@router.post("/plans/generate")
async def generate_plan(req: MealPlanCreate):
    return await svc.generate_plan(req)


@router.get("/plans")
async def list_plans(hijo_id: Optional[str] = None):
    return await svc.list_plans(hijo_id)


@router.get("/plans/{plan_id}")
async def get_plan(plan_id: str):
    try:
        return await svc.get_plan(plan_id)
    except PlanificationsError as e:
        raise HTTPException(404, str(e))


@router.get("/hijos/{hijo_id}/active-plan")
async def active_plan(hijo_id: str):
    plan = await svc.get_active_for_hijo(hijo_id)
    if not plan:
        return None
    return plan


@router.post("/plans/{plan_id}/items")
async def add_item(plan_id: str, item: MealItemAdd):
    try:
        return await svc.add_item(plan_id, item)
    except PlanificationsError as e:
        raise HTTPException(404, str(e))


@router.delete("/plans/{plan_id}/items/{idx}")
async def remove_item(plan_id: str, idx: int):
    try:
        return await svc.remove_item(plan_id, idx)
    except PlanificationsError as e:
        raise HTTPException(404, str(e))


@router.delete("/plans/{plan_id}")
async def delete_plan(plan_id: str):
    ok = await svc.delete_plan(plan_id)
    if not ok:
        raise HTTPException(404, "Plan no encontrado")
    return {"status": "deleted"}
