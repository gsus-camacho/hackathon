"""Feedback service: thumb voting + per-product aggregation + WhatsApp micro-ratings."""
from typing import Optional, List, Dict
from datetime import datetime, timezone
import uuid
import logging
from core.sqlite import get_db
from core.postgres import fetch_all
from integrations.twilio_client import send_whatsapp_text
from modules.feedback import repository as repo
from modules.feedback.schemas import ProductVote, VoteCreate
from modules.feedback.errors import InvalidRatingError
from modules.hijos import repository as hijos_repo
from modules.notifications import repository as notif_repo

logger = logging.getLogger(__name__)


async def vote(req: VoteCreate) -> Dict:
    if req.vote not in ("up", "down"):
        raise InvalidRatingError("vote must be 'up' or 'down'")
    v = ProductVote(**req.model_dump())
    doc = v.model_dump()
    await repo.insert_vote(doc)
    return doc


async def list_votes(product_name: Optional[str] = None, limit: int = 100) -> List[Dict]:
    return await repo.list_votes(product_name, limit)


async def per_product(nit_colegio: Optional[str] = None) -> List[Dict]:
    return await repo.aggregate_per_product(nit_colegio)


async def product_summary(product_name: str) -> Dict:
    return await repo.get_product_summary(product_name)


async def _rating_fingerprint(uid: str, product: str, day: str) -> str:
    return f"{uid}:{product}:{day}"


async def send_consumption_rating_requests(minutes: int = 25, limit: int = 40) -> List[Dict]:
    """Envía 👍/👎 por WhatsApp tras compras recientes."""
    q = """
        SELECT usuario_identificacion, nombre_estudiante, nombre_producto,
               CAST(precio AS NUMERIC) AS precio, nit_colegio, fecha::date AS sale_day
        FROM hackaton_ventas
        WHERE fecha >= NOW() - ($1::int * INTERVAL '1 minute')
        ORDER BY fecha DESC
        LIMIT $2
    """
    try:
        rows = await fetch_all(q, minutes, limit)
    except Exception as e:
        logger.error("rating sales query failed: %s", e)
        return []

    sent = []
    for row in rows:
        uid = row["usuario_identificacion"]
        product = row["nombre_producto"]
        day = str(row["sale_day"])
        fp = _rating_fingerprint(uid, product, day)
        existing = await get_db().rating_requests.find_one({"fingerprint": fp}, {"_id": 0})
        if existing:
            continue

        child = await hijos_repo.get_by_usuario(uid)
        phone = child.get("parent_phone") if child else None
        if not phone:
            continue

        student = row.get("nombre_estudiante") or child.get("nombre_estudiante", "tu hijo")
        body = (
            f"🍽️ *CONSUMO — BioAlert+*\n"
            f"{student} compró *{product}* (${float(row['precio'] or 0):,.0f}).\n"
            f"¿Cómo le pareció? Responde 👍 o 👎"
        )
        try:
            send_whatsapp_text(phone, body)
            req_doc = {
                "id": str(uuid.uuid4()),
                "fingerprint": fp,
                "usuario_identificacion": uid,
                "product_name": product,
                "parent_phone": phone,
                "identificacion_padre": child.get("identificacion_padre"),
                "nit_colegio": row.get("nit_colegio"),
                "status": "pending",
                "created_at": datetime.now(timezone.utc).isoformat(),
            }
            await get_db().rating_requests.insert_one(req_doc)
            await notif_repo.insert_notification(
                {
                    "id": str(uuid.uuid4()),
                    "kind": "consumption_rating",
                    "recipient_phone": phone,
                    "usuario_identificacion": uid,
                    "message": body,
                    "status": "sent",
                    "created_at": datetime.now(timezone.utc).isoformat(),
                }
            )
            sent.append(req_doc)
        except Exception as e:
            logger.error("rating request failed %s: %s", uid, e)
    return sent


async def try_whatsapp_rating(
    phone: str, message: str, identificacion_padre: Optional[str]
) -> Optional[str]:
    text = message.strip().lower()
    vote = None
    if text in ("👍", "👍🏻", "si", "sí", "bueno", "bien", "1", "up"):
        vote = "up"
    elif text in ("👎", "👎🏻", "no", "malo", "mal", "2", "down"):
        vote = "down"
    if not vote:
        return None

    pending = await get_db().rating_requests.find(
        {"parent_phone": phone, "status": "pending"}, {"_id": 0}
    ).sort("created_at", -1).to_list(1)
    if not pending and identificacion_padre:
        pending = await get_db().rating_requests.find(
            {"identificacion_padre": identificacion_padre, "status": "pending"}, {"_id": 0}
        ).sort("created_at", -1).to_list(1)
    if not pending:
        return "No hay consumos recientes pendientes de calificar."

    req = pending[0]
    v = ProductVote(
        product_name=req["product_name"],
        vote=vote,
        voter_id=req.get("usuario_identificacion"),
        nit_colegio=req.get("nit_colegio"),
        source="whatsapp",
    )
    await repo.insert_vote(v.model_dump())
    await get_db().rating_requests.update_one(
        {"id": req["id"]},
        {"$set": {"status": "answered", "vote": vote, "answered_at": datetime.now(timezone.utc).isoformat()}},
    )
    emoji = "👍" if vote == "up" else "👎"
    return f"{emoji} Gracias — registramos tu opinión sobre *{req['product_name']}*. Alimenta el Satisfaction Index de la cafetería."


async def summary(nit_colegio: Optional[str] = None) -> Dict:
    rows = await repo.aggregate_per_product(nit_colegio)
    total_up = sum(r["up"] for r in rows)
    total_down = sum(r["down"] for r in rows)
    total = total_up + total_down
    return {
        "total_votes": total,
        "up": total_up,
        "down": total_down,
        "average_score_pct": round((total_up / total * 100) if total else 0, 1),
        "products_voted": len(rows),
    }
