"""Product approval workflow: parent response + Gemini timeout fallback."""
from datetime import datetime, timezone, timedelta
from typing import Optional, List, Dict
import logging

from modules.approvals import repository as repo
from modules.approvals.schemas import ProductApproval, CatalogProductCreate, ApprovalResolve
from modules.approvals.errors import ApprovalsError
from modules.hijos import repository as hijos_repo
from modules.planifications import repository as plan_repo
from modules.notifications.schemas import SendMessageRequest
from modules.notifications import repository as notif_repo
from integrations.twilio_client import send_whatsapp_text
from integrations.gemini_client import chat_json

logger = logging.getLogger(__name__)

APPROVAL_TTL_HOURS = 24


async def _gemini_analyze(product_name: str, hijo_id: str) -> Dict:
    hijo = await hijos_repo.get_hijo(hijo_id)
    allergens = hijo.get("allergens", []) if hijo else []
    notes = hijo.get("notes", "") if hijo else ""
    nombre = hijo.get("nombre_estudiante", "estudiante") if hijo else "estudiante"
    prompt = (
        f"Producto: '{product_name}' para estudiante {nombre}. "
        f"Alérgenos: {', '.join(allergens) or 'ninguno'}. Notas: {notes or 'ninguna'}. "
        f"JSON: {{\"risk_level\":\"safe|unknown|risky\",\"reason\":\"...\",\"matched_allergens\":[]}}"
    )
    try:
        result = await chat_json(
            session_id=f"approval-{hijo_id}-{product_name}",
            system_message="Nutricionista escolar. Bloqueo conservador ante duda.",
            user_text=prompt,
        )
        return result if isinstance(result, dict) else {"risk_level": "unknown", "reason": "sin análisis"}
    except Exception as e:
        logger.warning("Gemini approval analysis failed: %s", e)
        return {"risk_level": "unknown", "reason": str(e), "matched_allergens": []}


async def create_from_plan_item(
    hijo_id: str,
    plan_id: str,
    plan_item_index: int,
    product_name: str,
    unit_price: float,
) -> Dict:
    hijo = await hijos_repo.get_hijo(hijo_id)
    if not hijo:
        raise ApprovalsError("Hijo no encontrado")
    expires = (datetime.now(timezone.utc) + timedelta(hours=APPROVAL_TTL_HOURS)).isoformat()
    approval = ProductApproval(
        hijo_id=hijo_id,
        usuario_identificacion=hijo["usuario_identificacion"],
        nombre_estudiante=hijo.get("nombre_estudiante", ""),
        identificacion_padre=hijo.get("identificacion_padre"),
        parent_phone=hijo.get("parent_phone"),
        nit_colegio=hijo.get("nit_colegio"),
        product_name=product_name,
        unit_price=unit_price,
        source="meal_plan",
        plan_id=plan_id,
        plan_item_index=plan_item_index,
        expires_at=expires,
    )
    doc = approval.model_dump()
    await repo.insert(doc)
    return doc


async def _remove_plan_item_if_needed(approval: Dict) -> None:
    plan_id = approval.get("plan_id")
    idx = approval.get("plan_item_index")
    if plan_id is None or idx is None:
        return
    plan = await plan_repo.get_meal_plan(plan_id)
    if not plan:
        return
    items = list(plan.get("items", []))
    if 0 <= idx < len(items):
        items.pop(idx)
        from modules.planifications.service import _compute_totals

        totals = _compute_totals(items, float(plan.get("minimum_budget", 0)))
        await plan_repo.update_meal_plan(
            plan_id,
            {
                "items": items,
                **totals,
                "updated_at": datetime.now(timezone.utc).isoformat(),
            },
        )


async def resolve(approval_id: str, decision: str, resolved_by: str = "dashboard") -> Dict:
    approval = await repo.get(approval_id)
    if not approval:
        raise ApprovalsError("Solicitud no encontrada")
    if approval.get("status") != "pending":
        return approval

    now = datetime.now(timezone.utc).isoformat()
    if decision == "block":
        await _remove_plan_item_if_needed(approval)
        status = "blocked"
    else:
        status = "allowed"

    return await repo.update(
        approval_id,
        {"status": status, "resolved_at": now, "resolved_by": resolved_by},
    )


async def resolve_for_parent(identificacion_padre: str, decision: str) -> Optional[Dict]:
    approval = await repo.find_latest_pending_for_parent(identificacion_padre)
    if not approval:
        return None
    return await resolve(approval["id"], decision, resolved_by="whatsapp_parent")


async def process_expired(limit: int = 30) -> List[Dict]:
    """Pilar 2: sin respuesta del padre → Gemini decide; bloqueo conservador si risky."""
    now = datetime.now(timezone.utc).isoformat()
    expired = await repo.list_expired_pending(now, limit=limit)
    results = []
    for approval in expired:
        analysis = await _gemini_analyze(approval["product_name"], approval["hijo_id"])
        risk = analysis.get("risk_level", "unknown")
        if risk == "risky" or risk == "unknown":
            await _remove_plan_item_if_needed(approval)
            status = "auto_blocked"
        else:
            status = "auto_allowed"
        doc = await repo.update(
            approval["id"],
            {
                "status": status,
                "resolved_at": now,
                "resolved_by": "gemini_timeout",
                "gemini_risk_level": risk,
                "gemini_reason": analysis.get("reason"),
            },
        )
        results.append(doc)
    return results


async def register_catalog_product(req: CatalogProductCreate) -> Dict:
    """Cafetería añade producto nuevo → cola de aprobación por cada hijo del colegio."""
    import uuid

    catalog_doc = {
        "id": str(uuid.uuid4()),
        "product_name": req.product_name,
        "nit_colegio": req.nit_colegio,
        "colegio": req.colegio,
        "unit_price": req.unit_price,
        "category": req.category,
        "created_at": datetime.now(timezone.utc).isoformat(),
    }
    await repo.insert_catalog(catalog_doc)

    hijos = await hijos_repo.list_hijos(nit_colegio=req.nit_colegio, limit=500)
    approvals = []
    for hijo in hijos:
        expires = (datetime.now(timezone.utc) + timedelta(hours=APPROVAL_TTL_HOURS)).isoformat()
        approval = ProductApproval(
            hijo_id=hijo["id"],
            usuario_identificacion=hijo["usuario_identificacion"],
            nombre_estudiante=hijo.get("nombre_estudiante", ""),
            identificacion_padre=hijo.get("identificacion_padre"),
            parent_phone=hijo.get("parent_phone"),
            nit_colegio=req.nit_colegio,
            product_name=req.product_name,
            unit_price=req.unit_price,
            source="catalog_new",
            expires_at=expires,
        )
        doc = approval.model_dump()
        await repo.insert(doc)
        approvals.append(doc)
        phone = hijo.get("parent_phone")
        if phone:
            body = (
                f"🆕 *NUEVO PRODUCTO — BioAlert+*\n\n"
                f"La cafetería añadió *{req.product_name}* al catálogo "
                f"para {hijo.get('nombre_estudiante', 'tu hijo')}.\n\n"
                f"Responde *PERMITIR* o *BLOQUEAR*.\n"
                f"Sin respuesta en 24h, Gemini analizará compatibilidad (Pilar 2)."
            )
            try:
                send_whatsapp_text(phone, body)
                await notif_repo.insert_notification(
                    {
                        "id": str(uuid.uuid4()),
                        "kind": "catalog_new_product",
                        "recipient_phone": phone,
                        "identificacion_padre": hijo.get("identificacion_padre"),
                        "usuario_identificacion": hijo["usuario_identificacion"],
                        "message": body,
                        "status": "sent",
                        "created_at": datetime.now(timezone.utc).isoformat(),
                    }
                )
            except Exception as e:
                logger.error("Catalog notify failed %s: %s", phone, e)

    return {"catalog": catalog_doc, "approvals_created": len(approvals), "approvals": approvals[:20]}


async def list_pending(
    identificacion_padre: Optional[str] = None,
    nit_colegio: Optional[str] = None,
    limit: int = 100,
) -> List[Dict]:
    return await repo.list_pending(identificacion_padre, nit_colegio, limit)
