"""Planifications service: balance prediction + weekly meal planner with reward."""
from typing import Optional, List, Dict
from datetime import datetime, timezone
import logging
from modules.planifications import repository as repo
from modules.planifications.schemas import MealPlan, MealPlanCreate, MealItem, MealItemAdd
from modules.planifications.errors import PlanificationsError, AllergenConflictError
from modules.hijos import repository as hijos_repo
from modules.statistics import repository as stats_repo
from modules.recommendations import service as rec_svc
from integrations.gemini_client import chat_json
from integrations.twilio_client import send_whatsapp_text

logger = logging.getLogger(__name__)

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


async def _validate_product_allergens(hijo_id: str, product_name: str) -> List[str]:
    """Check if product conflicts with student allergens. Returns matched allergens."""
    hijo = await hijos_repo.get_hijo(hijo_id)
    if not hijo:
        return []
    usuario_identificacion = hijo.get("usuario_identificacion")
    if not usuario_identificacion:
        return []
    matched = await rec_svc.check_allergen_risk(usuario_identificacion, product_name)
    return matched


async def _notify_parent_new_product(hijo_id: str, product_name: str, unit_price: float, day: int, plan_id: str) -> None:
    """Send WhatsApp notification to parent about new product added to plan (Pilar 1)."""
    try:
        hijo = await hijos_repo.get_hijo(hijo_id)
        if not hijo:
            logger.warning(f"Hijo {hijo_id} not found for notification")
            return
        parent_phone = hijo.get("parent_phone")
        identificacion_padre = hijo.get("identificacion_padre")
        nombre_estudiante = hijo.get("nombre_estudiante") or "tu hijo"
        if not parent_phone and identificacion_padre:
            # Try to look up phone from parent auth
            try:
                from core.postgres import fetch_one
                parent_info = await fetch_one(
                    "SELECT telefono, whatsapp FROM hackaton_padres_auth WHERE identificacion_padre=$1",
                    identificacion_padre,
                )
                if parent_info:
                    parent_phone = parent_info.get("telefono") or parent_info.get("whatsapp")
            except Exception as e:
                logger.warning(f"Could not look up parent phone: {e}")
        if not parent_phone:
            logger.info(f"No parent phone for hijo {hijo_id}, skipping notification")
            return
        days_of_week = ["Lunes", "Martes", "Miércoles", "Jueves", "Viernes", "Sábado", "Domingo"]
        day_name = days_of_week[day] if 0 <= day < 7 else f"Día {day}"
        body = (
            f"🆕 *BioAlert+ — Nuevo producto en el plan*\n\n"
            f"Se ha asignado *{product_name}* (${unit_price:,.0f}) "
            f"a {nombre_estudiante} para el *{day_name}*.\n\n"
            f"🔹 ¿Quieres bloquear este producto? Responde BLOQUEAR\n"
            f"🔹 ¿Quieres permitirlo? Responde PERMITIR\n"
            f"🔹 Si no respondes, el sistema analizará automáticamente "
            f"si es seguro para {nombre_estudiante} (Pilar 2)."
        )
        resp = send_whatsapp_text(parent_phone, body)
        logger.info(f"New product notification sent to {parent_phone}: {resp.get('status', 'sent')}")
        # Log as notification
        try:
            from modules.notifications.schemas import Notification
            from modules.notifications import service as notif_svc
            notif = Notification(
                kind="new_plan_product",
                recipient_phone=parent_phone,
                usuario_identificacion=hijo.get("usuario_identificacion"),
                message=body,
                twilio_sid=resp.get("sid", ""),
                status=resp.get("status", "sent"),
            )
            await notif_svc.send_text.__wrapped__(notif)
        except Exception as e:
            logger.warning(f"Could not log notification: {e}")
    except Exception as e:
        logger.error(f"Failed to send new product notification: {e}")


async def _analyze_with_gemini(product_name: str, hijo_id: str) -> Dict:
    """Use Gemini API to analyze product composition against student profile (Pilar 2)."""
    hijo = await hijos_repo.get_hijo(hijo_id)
    allergens = hijo.get("allergens", []) if hijo else []
    notes = hijo.get("notes", "") if hijo else ""
    nombre = hijo.get("nombre_estudiante", "estudiante") if hijo else "estudiante"
    prompt = (
        f"Eres un nutricionista escolar experto en seguridad alimentaria.\n\n"
        f"Un nuevo producto '{product_name}' va a ser añadido al plan semanal "
        f"del estudiante {nombre}.\n\n"
        f"Perfil del estudiante:\n"
        f"- Alérgenos registrados: {', '.join(allergens) if allergens else 'Ninguno'}\n"
        f"- Notas adicionales: {notes if notes else 'Ninguna'}\n\n"
        f"Analiza el nombre del producto '{product_name}' y su composición inferida. "
        f"Determina si existe riesgo de incompatibilidad con el perfil del estudiante.\n\n"
        f"Devuelve SOLO JSON:\n"
        f'{{"risk_level": "safe|unknown|risky", "reason": "breve explicación", '
        f'"matched_allergens": ["alergeno1", ...]}}'
    )
    try:
        result = await chat_json(
            session_id=f"allergen-analyze-{hijo_id}-{datetime.now(timezone.utc).timestamp()}",
            system_message="Eres un nutricionista escolar experto en seguridad alimentaria.",
            user_text=prompt,
        )
        if isinstance(result, dict):
            return result
        return {"risk_level": "unknown", "reason": "No se pudo analizar", "matched_allergens": []}
    except Exception as e:
        logger.warning(f"Gemini analysis failed: {e}")
        return {"risk_level": "unknown", "reason": "Error en análisis", "matched_allergens": []}


async def create_plan(req: MealPlanCreate) -> Dict:
    plan = MealPlan(**req.model_dump())
    doc = plan.model_dump()
    doc.update(_compute_totals(doc["items"], doc["minimum_budget"]))
    await repo.insert_meal_plan(doc)
    return doc


async def generate_plan(req: MealPlanCreate) -> Dict:
    if req.items:
        return await create_plan(req)

    hijo = await hijos_repo.get_hijo(req.hijo_id)
    if not hijo:
        raise PlanificationsError("Hijo no encontrado")

    usuario_identificacion = hijo.get("usuario_identificacion")
    nombre_estudiante = hijo.get("nombre_estudiante") or ""
    child_allergens = hijo.get("allergens", [])
    top_products = await stats_repo.get_student_top_product_prices(usuario_identificacion, limit=10, days=30)

    # FILTER: Exclude products that match child's allergens (Pilar 2)
    safe_products = []
    for product in top_products:
        matched = await _validate_product_allergens(req.hijo_id, product["name"])
        if not matched:
            safe_products.append(product)

    items = []
    for index, product in enumerate(safe_products[:5]):
        items.append(
            MealItem(
                day=index,
                product_name=product["name"],
                quantity=1,
                unit_price=round(product["avg_price"], 2),
            )
        )

    if not items:
        fallback_price = round(req.minimum_budget / 5, 2)
        items = [
            MealItem(day=i, product_name=f"Producto {i + 1}", quantity=1, unit_price=fallback_price)
            for i in range(5)
        ]

    plan = MealPlan(
        hijo_id=req.hijo_id,
        usuario_identificacion=usuario_identificacion,
        nombre_estudiante=nombre_estudiante,
        week_start=req.week_start,
        minimum_budget=req.minimum_budget,
        items=items,
    )
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

    hijo_id = plan.get("hijo_id")

    # PILAR 2: Validate against allergens first
    matched_allergens = await _validate_product_allergens(hijo_id, item.product_name)
    if matched_allergens:
        raise AllergenConflictError(
            f"El producto '{item.product_name}' contiene alérgenos "
            f"incompatibles con el perfil del estudiante: {', '.join(matched_allergens)}. "
            f"Bloqueado automáticamente por seguridad."
        )

    # PILAR 2: Defer to Gemini analysis for safety check
    gemini_result = await _analyze_with_gemini(item.product_name, hijo_id)
    risk_level = gemini_result.get("risk_level", "unknown")
    gemini_allergens = gemini_result.get("matched_allergens", [])

    if risk_level == "risky":
        raise AllergenConflictError(
            f"El análisis automático (Gemini) detectó un posible riesgo "
            f"con '{item.product_name}': {gemini_result.get('reason', 'incompatibilidad detectada')}. "
            f"Bloqueado por defecto para seguridad del estudiante."
        )

    items = list(plan.get("items", []))
    items.append(item.model_dump())
    totals = _compute_totals(items, float(plan.get("minimum_budget", 0)))
    updates = {
        "items": items,
        **totals,
        "updated_at": datetime.now(timezone.utc).isoformat(),
    }
    doc = await repo.update_meal_plan(plan_id, updates)

    # PILAR 1: Send WhatsApp notification to parent
    await _notify_parent_new_product(
        hijo_id=hijo_id,
        product_name=item.product_name,
        unit_price=item.unit_price,
        day=item.day,
        plan_id=plan_id,
    )

    enh = dict(doc or {})
    if gemini_allergens:
        enh["_allergen_warning"] = gemini_allergens
    return enh if enh else doc


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