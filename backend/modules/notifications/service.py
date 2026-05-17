"""Notifications service: WhatsApp send + ConversationHandler with Gemini."""
from typing import Optional, Dict, List
from datetime import datetime, timezone
import logging
from modules.notifications import repository as repo
from modules.notifications.schemas import Notification, SendMessageRequest, BotSession
from modules.notifications.errors import WhatsAppDeliveryError
from integrations.twilio_client import send_whatsapp_text, send_whatsapp_template
from integrations.gemini_client import chat_send, chat_json
from modules.planifications import service as plan_svc
from modules.planifications import repository as plan_repo
from modules.discounts import service as disc_svc
from modules.recommendations import service as rec_svc
from modules.statistics import repository as stats_repo
from modules.hijos import repository as hijos_repo

logger = logging.getLogger(__name__)


# ----- Outbound notifications -----

async def send_text(req: SendMessageRequest) -> Dict:
    try:
        resp = send_whatsapp_text(req.to, req.body)
        notif = Notification(
            kind=req.kind,
            recipient_phone=req.to,
            recipient_name=req.recipient_name,
            usuario_identificacion=req.usuario_identificacion,
            identificacion_padre=req.identificacion_padre,
            message=req.body,
            twilio_sid=resp["sid"],
            status=resp["status"],
        )
    except Exception as e:
        notif = Notification(
            kind=req.kind,
            recipient_phone=req.to,
            recipient_name=req.recipient_name,
            usuario_identificacion=req.usuario_identificacion,
            identificacion_padre=req.identificacion_padre,
            message=req.body,
            status="failed",
            error=str(e),
        )
        doc = notif.model_dump()
        await repo.insert_notification(doc)
        raise WhatsAppDeliveryError(str(e))
    doc = notif.model_dump()
    await repo.insert_notification(doc)
    return doc


async def send_low_balance_alert(phone: str, name: str, balance: float, days: int) -> Dict:
    body = (
        f"🔔 *BioAlert+* — Hola {name}, el saldo del estudiante está bajo (${balance:,.0f}). "
        f"Estimamos que durará ~{days} días. Recarga para evitar interrupciones."
    )
    req = SendMessageRequest(to=phone, body=body, kind="low_balance", recipient_name=name)
    return await send_text(req)


async def send_allergen_alert(phone: str, parent: str, student: str, product: str, allergens: List[str]) -> Dict:
    body = (
        f"⚠️ *ALERTA ALERGENO* — {parent}, hoy se intentó vender '{product}' a {student}. "
        f"Detectamos alergenos registrados: {', '.join(allergens)}. La transacción quedó marcada para revisión."
    )
    req = SendMessageRequest(to=phone, body=body, kind="allergen_alert", recipient_name=parent)
    return await send_text(req)


async def _send_low_balance_alerts(nit_colegio: Optional[str] = None, threshold_days: int = 2) -> List[Dict]:
    alerts = []
    risks = await plan_svc.students_at_risk(nit_colegio)
    for student in risks:
        child = await hijos_repo.get_by_usuario(student["usuario_identificacion"])
        if not child or not child.get("parent_phone"):
            continue
        parent_name = child.get("nombre_padre") or child.get("parent_phone")
        try:
            alerts.append(
                await send_low_balance_alert(
                    phone=child["parent_phone"],
                    name=parent_name,
                    balance=student["current_balance"],
                    days=student["days_remaining"],
                )
            )
        except Exception as e:
            logger.error("Low balance alert failed for %s: %s", student["usuario_identificacion"], e)
    return alerts


async def _send_allergen_alerts(days: int = 1) -> List[Dict]:
    sent = []
    allergens = await rec_svc.list_allergens()
    for profile in allergens:
        usuario = profile["usuario_identificacion"]
        child = await hijos_repo.get_by_usuario(usuario)
        if not child or not child.get("parent_phone"):
            continue
        purchases = await stats_repo.get_student_recent_purchases(usuario, days=days, limit=20)
        for purchase in purchases:
            matched = await rec_svc.check_allergen_risk(usuario, purchase["product"])
            if matched.get("risk"):
                try:
                    sent.append(
                        await send_allergen_alert(
                            phone=child["parent_phone"],
                            parent=child.get("nombre_padre") or "Padre/Madre",
                            student=child.get("nombre_estudiante") or "Estudiante",
                            product=purchase["product"],
                            allergens=matched.get("matched", []),
                        )
                    )
                except Exception as e:
                    logger.error("Allergen alert failed for %s: %s", usuario, e)
                break
    return sent


async def _send_weekly_nutrition_report() -> List[Dict]:
    reports = []
    hijos = await hijos_repo.list_hijos()
    for child in hijos:
        phone = child.get("parent_phone")
        if not phone:
            continue
        usuario = child["usuario_identificacion"]
        avg_spend = await stats_repo.get_student_avg_spend(usuario, days=7)
        top_products = await stats_repo.get_student_top_products(usuario, limit=3, days=7)
        products = ", ".join([p["name"] for p in top_products]) or "sin datos recientes"
        body = (
            f"📊 *Resumen semanal de BioAlert+*\n"
            f"{child.get('nombre_estudiante', 'Tu hijo')} gastó en promedio ${avg_spend:,.0f}/día.\n"
            f"Top productos: {products}.\n"
            "Te recomendamos revisar el plan semanal si quieres reducir gastos." 
        )
        try:
            reports.append(
                await send_text(
                    SendMessageRequest(
                        to=phone,
                        body=body,
                        kind="weekly_nutrition",
                        recipient_name=child.get("nombre_padre"),
                        usuario_identificacion=usuario,
                        identificacion_padre=child.get("identificacion_padre"),
                        nit_colegio=child.get("nit_colegio"),
                    )
                )
            )
        except Exception as e:
            logger.error("Weekly nutrition report failed for %s: %s", usuario, e)
    return reports


# ----- Inbound conversation handler -----

INTENT_SYSTEM = """Eres BioBot, asistente de WhatsApp de BioAlert+ para padres de familia colombianos.
Clasifica el mensaje del usuario en una de estas intenciones:
- consumption: el padre pregunta qué compró su hijo, qué consumió, qué comió
- balance: pregunta sobre saldo, dinero, recarga
- package: pregunta por paquetes, ofertas, descuentos, combos
- alerts: alergenos, alertas, seguridad
- greeting: saludo o conversación social
- unknown: cualquier otra cosa

Devuelve SOLO JSON: {"intent": "consumption|balance|package|alerts|greeting|unknown", "student_query": "string opcional con nombre/id si lo mencionan"}"""

REPLY_SYSTEM = """Eres BioBot, asistente cálido y conciso de BioAlert+ en WhatsApp para padres en Colombia.
Responde en español neutro, máximo 4 líneas, con emoji discreto.
Usa la información de datos enviada para dar respuesta concreta y útil."""


def simple_intent_detection(message: str) -> Dict[str, str]:
    text = message.lower()
    if any(k in text for k in ["qué comió", "que comió", "consumió", "comió", "hoy comió", "consumo"]):
        return {"intent": "consumption"}
    if any(k in text for k in ["saldo", "recarga", "dinero", "cuánto me queda", "me queda", "saldo bajo", "re carga"]):
        return {"intent": "balance"}
    if any(k in text for k in ["paquete", "oferta", "combo", "descuento", "promoción", "promocion"]):
        return {"intent": "package"}
    if any(k in text for k in ["alerg", "alergia", "maní", "mani", "gluten", "soya", "soja", "nuez", "marisco", "alerta"]):
        return {"intent": "alerts"}
    if any(k in text for k in ["hola", "buenos", "buenas", "gracias", "qué tal", "hey", "buen dia", "buen día"]):
        return {"intent": "greeting"}
    return {"intent": "unknown"}


def _extract_parent_id(message: str) -> Optional[str]:
    import re
    match = re.search(r"\b(\d{8,15})\b", message)
    return match.group(1) if match else None


async def _student_consumption_summary(identificacion_padre: Optional[str]) -> str:
    if not identificacion_padre:
        return "No se encuentra el padre asociado al número."
    students = await plan_repo.get_parent_students(identificacion_padre)
    if not students:
        return "No encontré estudiantes vinculados."
    lines = []
    for s in students[:2]:
        bal = await plan_svc.predict_balance(s["usuario_identificacion"])
        purchases = await stats_repo.get_student_recent_purchases(s["usuario_identificacion"], days=1, limit=5)
        purchases_text = "; ".join(
            f"{p['quantity']}x {p['product']} (${p['total']:,.0f})" for p in purchases[:3]
        ) or "Sin compras registradas hoy"
        lines.append(
            f"{s['nombre_estudiante']}: saldo ${bal['current_balance']:,.0f}, {bal['days_remaining']} días restantes. Últimas compras: {purchases_text}"
        )
    return " \n".join(lines)


async def _student_balance_summary(identificacion_padre: Optional[str]) -> str:
    if not identificacion_padre:
        return "No se encuentra el padre asociado al número."
    students = await plan_repo.get_parent_students(identificacion_padre)
    if not students:
        return "No encontré estudiantes vinculados."
    lines = []
    for s in students[:2]:
        bal = await plan_svc.predict_balance(s["usuario_identificacion"])
        lines.append(
            f"{s['nombre_estudiante']}: ${bal['current_balance']:,.0f} - ~{bal['days_remaining']} días ({bal['risk_level']})."
        )
    return " \n".join(lines)


async def _package_suggestions(identificacion_padre: Optional[str]) -> str:
    if not identificacion_padre:
        return "Primero necesito identificarte como padre para ofrecer paquetes personalizados."
    students = await plan_repo.get_parent_students(identificacion_padre)
    if not students:
        return "No encontré estudiantes vinculados a tu cuenta."
    first_student = students[0]
    offer = await rec_svc.package_offer(first_student["usuario_identificacion"], first_student.get("nit_colegio"))
    lines = [
        f"{offer['weekly']['name']}: ${offer['weekly']['price']:,.0f} (-{offer['weekly']['discount_pct']}%)",
        f"{offer['monthly']['name']}: ${offer['monthly']['price']:,.0f} (-{offer['monthly']['discount_pct']}%)",
    ]
    return "\n".join(lines)


async def _alert_context(identificacion_padre: Optional[str]) -> str:
    allergens = await rec_svc.list_allergens()
    if not allergens:
        return "No hay perfiles de alérgenos registrados aún."
    lines = [
        f"{a.get('nombre_estudiante', 'Estudiante')}: {', '.join(a.get('allergens', []))}"
        for a in allergens[:5]
    ]
    return "\n".join(lines)


async def detect_intent(message: str) -> Dict:
    return simple_intent_detection(message)


async def handle_incoming(phone: str, body: str, profile_name: Optional[str] = None) -> str:
    # Find session
    session = await repo.get_session_by_phone(phone) or {
        "phone": phone,
        "messages": [],
        "created_at": datetime.now(timezone.utc).isoformat(),
    }
    identificacion_padre = session.get("identificacion_padre") or _extract_parent_id(body)
    if identificacion_padre and identificacion_padre != session.get("identificacion_padre"):
        session["identificacion_padre"] = identificacion_padre

    intent_data = await detect_intent(body)
    intent = intent_data.get("intent", "unknown")

    if intent == "consumption":
        reply = await _student_consumption_summary(identificacion_padre)
        if reply.startswith("No se encuentra"):
            reply = "Hola 👋 puedes decirme el número de cédula del padre o preguntar: ¿qué comió mi hijo hoy?"
    elif intent == "balance":
        reply = await _student_balance_summary(identificacion_padre)
    elif intent == "package":
        reply = await _package_suggestions(identificacion_padre)
    elif intent == "alerts":
        reply = await _alert_context(identificacion_padre)
    elif intent == "greeting":
        reply = "Hola 👋 soy BioBot de BioAlert+. Pregúntame por 'consumo', 'saldo', 'paquetes' o 'alertas'."
    else:
        reply = "Hola 👋 puedo ayudarte a ver saldo, recomendaciones de paquetes y alertas de alérgenos. Escribe 'saldo' o 'paquetes'."

    if intent in ["consumption", "balance"] and "saldo" not in reply.lower() and len(reply) < 30:
        reply = reply + "\nTambién puedes preguntar: '¿qué comió mi hijo hoy?'"

    session_messages = session.get("messages", [])
    session_messages.append({"role": "user", "text": body, "ts": datetime.now(timezone.utc).isoformat()})
    session_messages.append({"role": "bot", "text": reply, "ts": datetime.now(timezone.utc).isoformat(), "intent": intent})
    session.update({
        "messages": session_messages[-20:],
        "last_intent": intent,
        "updated_at": datetime.now(timezone.utc).isoformat(),
    })
    await repo.upsert_session(session)

    try:
        if not phone.startswith("whatsapp:test"):
            send_resp = send_whatsapp_text(phone, reply)
            notif = Notification(
                kind="custom",
                recipient_phone=phone,
                message=reply,
                twilio_sid=send_resp["sid"],
                status=send_resp["status"],
            )
            await repo.insert_notification(notif.model_dump())
    except Exception as e:
        logger.error("Failed to send WhatsApp reply: %s", e)
    return reply

    # Save outbound
    try:
        if not phone.startswith("whatsapp:test"):
            send_resp = send_whatsapp_text(phone, reply)
            notif = Notification(
                kind="custom",
                recipient_phone=phone,
                message=reply,
                twilio_sid=send_resp["sid"],
                status=send_resp["status"],
            )
            await repo.insert_notification(notif.model_dump())
    except Exception as e:
        logger.error("Failed to send WhatsApp reply: %s", e)
    return reply


async def list_recent(limit: int = 50) -> List[Dict]:
    return await repo.list_notifications(limit)


async def list_sessions(limit: int = 50) -> List[Dict]:
    return await repo.list_sessions(limit)
