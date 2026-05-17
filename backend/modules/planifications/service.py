"""Planifications service: balance prediction + weekly meal planner with reward."""
from typing import Optional, List, Dict
from datetime import datetime, timezone
from modules.planifications import repository as repo
from modules.planifications.schemas import MealPlan, MealPlanCreate, MealItem, MealItemAdd
from modules.planifications.errors import PlanificationsError


# -- Balance prediction --

async def predict_balance(usuario_identificacion: str) -> Optional[Dict]:
    bal = await repo.get_student_balance(usuario_identificacion)
    if not bal:
        return None
    total_recargas = float(bal.get("total_recargas") or 0)
    total_consumo = float(bal.get("total_consumo") or 0)
    current = total_recargas - total_consumo
    avg_daily = max(total_consumo / 60.0, 100.0)
    days_remaining = int(current / avg_daily) if avg_daily > 0 else 0
    risk = "high" if days_remaining < 3 else ("medium" if days_remaining < 7 else "low")
    return {
        "usuario_identificacion": usuario_identificacion,
        "nombre_estudiante": bal.get("nombre_estudiante") or "",
        "nit_colegio": bal.get("nit_colegio"),
        "current_balance": round(current, 2),
        "avg_daily_spend": round(avg_daily, 2),
        "days_remaining": max(days_remaining, 0),
        "risk_level": risk,
        "last_recharge_date": str(bal.get("last_recharge")) if bal.get("last_recharge") else None,
        "last_consumption_date": str(bal.get("last_consumption")) if bal.get("last_consumption") else None,
    }


async def students_at_risk(nit_colegio: Optional[str] = None, limit: int = 50) -> List[Dict]:
    rows = await repo.list_students_at_risk_fast(nit_colegio, limit)
    out = []
    for r in rows:
        recargas = float(r.get("total_recargas") or 0)
        consumo = float(r.get("total_consumo") or 0)
        current = recargas - consumo
        avg_daily = max(consumo / 60.0, 100.0)
        days_remaining = int(current / avg_daily) if avg_daily > 0 else 0
        risk = "high" if days_remaining < 3 else ("medium" if days_remaining < 7 else "low")
        out.append({
            "usuario_identificacion": r["usuario_identificacion"],
            "nombre_estudiante": r.get("nombre_estudiante") or "",
            "nit_colegio": r.get("nit_colegio"),
            "current_balance": round(current, 2),
            "avg_daily_spend": round(avg_daily, 2),
            "days_remaining": max(days_remaining, 0),
            "risk_level": risk,
            "last_consumption_date": str(r.get("last_consumption")) if r.get("last_consumption") else None,
            "last_recharge_date": str(r.get("last_recharge")) if r.get("last_recharge") else None,
        })
    return out


async def search_students(query: str, limit: int = 20) -> List[Dict]:
    return await repo.search_students(query, limit)


# -- Weekly meal planner --

def _compute_totals(items: List[Dict], minimum_budget: float) -> Dict:
    current_total = sum(float(i.get("unit_price", 0)) * int(i.get("quantity", 1)) for i in items)
    goal_met = current_total >= minimum_budget and minimum_budget > 0
    reward = None
    if goal_met:
        reward = "10% descuento próxima recarga"
    return {"current_total": round(current_total, 2), "goal_met": goal_met, "reward": reward}


async def create_plan(req: MealPlanCreate) -> Dict:
    plan = MealPlan(**req.model_dump())
    doc = plan.model_dump()
    doc.update(_compute_totals(doc["items"], doc["minimum_budget"]))
    await repo.insert_meal_plan(doc)
    return doc


async def list_plans(hijo_id: Optional[str] = None) -> List[Dict]:
    return await repo.list_meal_plans(hijo_id)


async def get_plan(plan_id: str) -> Dict:
    doc = await repo.get_meal_plan(plan_id)
    if not doc:
        raise PlanificationsError("Plan no encontrado")
    return doc


async def get_active_for_hijo(hijo_id: str) -> Optional[Dict]:
    return await repo.get_active_plan_for_hijo(hijo_id)


async def add_item(plan_id: str, item: MealItemAdd) -> Dict:
    plan = await repo.get_meal_plan(plan_id)
    if not plan:
        raise PlanificationsError("Plan no encontrado")
    items = list(plan.get("items", []))
    items.append(item.model_dump())
    totals = _compute_totals(items, float(plan.get("minimum_budget", 0)))
    updates = {
        "items": items,
        **totals,
        "updated_at": datetime.now(timezone.utc).isoformat(),
    }
    doc = await repo.update_meal_plan(plan_id, updates)
    return doc


async def remove_item(plan_id: str, idx: int) -> Dict:
    plan = await repo.get_meal_plan(plan_id)
    if not plan:
        raise PlanificationsError("Plan no encontrado")
    items = list(plan.get("items", []))
    if 0 <= idx < len(items):
        items.pop(idx)
    totals = _compute_totals(items, float(plan.get("minimum_budget", 0)))
    updates = {
        "items": items,
        **totals,
        "updated_at": datetime.now(timezone.utc).isoformat(),
    }
    return await repo.update_meal_plan(plan_id, updates)


async def delete_plan(plan_id: str) -> bool:
    return await repo.delete_meal_plan(plan_id)
