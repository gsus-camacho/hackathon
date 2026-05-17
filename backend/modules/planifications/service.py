"""Planifications service: balance & consumption prediction."""
from typing import Optional, List, Dict
from datetime import datetime, timezone
from modules.planifications import repository as repo
from modules.planifications.schemas import BalancePrediction, StudentBalance


async def predict_balance(usuario_identificacion: str) -> Optional[Dict]:
    bal = await repo.get_student_balance(usuario_identificacion)
    if not bal:
        return None
    total_recargas = float(bal.get("total_recargas") or 0)
    total_consumo = float(bal.get("total_consumo") or 0)
    current = total_recargas - total_consumo
    # rough average daily spend based on history of last 60 days approximation
    last_v = bal.get("last_consumption")
    last_r = bal.get("last_recharge")
    # Compute average daily by total_consumo / days observed
    days_observed = 60
    avg_daily = max(total_consumo / max(days_observed, 1), 100.0)
    days_remaining = int(current / avg_daily) if avg_daily > 0 else 0
    risk = "low"
    if days_remaining < 3:
        risk = "high"
    elif days_remaining < 7:
        risk = "medium"
    return {
        "usuario_identificacion": usuario_identificacion,
        "nombre_estudiante": bal.get("nombre_estudiante") or "",
        "nit_colegio": bal.get("nit_colegio"),
        "current_balance": round(current, 2),
        "avg_daily_spend": round(avg_daily, 2),
        "days_remaining": max(days_remaining, 0),
        "risk_level": risk,
        "last_recharge_date": str(last_r) if last_r else None,
        "last_consumption_date": str(last_v) if last_v else None,
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
