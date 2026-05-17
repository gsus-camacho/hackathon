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


async def detect_intent(message: str) -> Dict:
    try:
        result = await chat_json(
            session_id=f"intent-{datetime.now(timezone.utc).timestamp()}",
            system_message=INTENT_SYSTEM,
            user_text=message,
        )
        return result if isinstance(result, dict) else {"intent": "unknown"}
    except Exception as e:
        logger.warning("intent detection failed: %s", e)
        return {"intent": "unknown"}


async def _consumption_context(identificacion_padre: Optional[str]) -> str:
    if not identificacion_padre:
        return "(no se identificó al padre por número de teléfono)"
    students = await plan_repo.get_parent_students(identificacion_padre)
    if not students:
        return "No encontré estudiantes vinculados."
    out = []
    for s in students[:3]:
        bal = await plan_svc.predict_balance(s["usuario_identificacion"])
        if bal:
            out.append(
                f"- {s['nombre_estudiante']} ({s['colegio']}): saldo ${bal['current_balance']:,.0f}, "
                f"~{bal['days_remaining']} días, último consumo {bal['last_consumption_date']}"
            )
    return "\n".join(out) if out else "Sin datos recientes."


async def handle_incoming(phone: str, body: str, profile_name: Optional[str] = None) -> str:
    # Find session
    session = await repo.get_session_by_phone(phone) or {
        "phone": phone,
        "messages": [],
        "created_at": datetime.now(timezone.utc).isoformat(),
    }
    identificacion_padre = session.get("identificacion_padre")
    # Detect intent
    intent_data = await detect_intent(body)
    intent = intent_data.get("intent", "unknown")

    # Build data context
    if intent == "consumption":
        context = await _consumption_context(identificacion_padre)
        data_block = f"DATOS DE CONSUMO:\n{context}"
    elif intent == "balance":
        context = await _consumption_context(identificacion_padre)
        data_block = f"SALDO Y PREDICCION:\n{context}"
    elif intent == "package":
        pkgs = await disc_svc.list_packages()
        if not pkgs:
            pkgs = await disc_svc.generate_and_save()
        lines = [
            f"- {p['name']}: ${p['discounted_total']:,.0f} ({p['discount_pct']}% off)"
            for p in pkgs[:3]
        ]
        data_block = "PAQUETES VIGENTES:\n" + ("\n".join(lines) if lines else "Sin paquetes activos.")
    elif intent == "alerts":
        allergens = await rec_svc.list_allergens()
        recent = allergens[:3]
        if recent:
            lines = [
                f"- {a.get('nombre_estudiante', 'Estudiante')}: {', '.join(a.get('allergens', []))}"
                for a in recent
            ]
            data_block = "PERFILES ALERGENOS RECIENTES:\n" + "\n".join(lines)
        else:
            data_block = "No hay perfiles de alergenos registrados aún."
    else:
        data_block = "Saluda y ofrece menú: 'consumo', 'saldo', 'paquetes', 'alertas'."

    user_prompt = (
        f"Mensaje del padre ({profile_name or phone}): \"{body}\"\n"
        f"Intent detectado: {intent}\n\n{data_block}\n\nResponde."
    )
    try:
        reply = await chat_send(
            session_id=f"reply-{phone}",
            system_message=REPLY_SYSTEM,
            user_text=user_prompt,
        )
    except Exception as e:
        logger.error("Gemini reply failed: %s", e)
        reply = "Hola 👋 soy BioBot. Pregúntame sobre 'consumo', 'saldo', 'paquetes' o 'alertas'."

    # Persist session
    msgs = session.get("messages", [])
    msgs.append({"role": "user", "text": body, "ts": datetime.now(timezone.utc).isoformat()})
    msgs.append({"role": "bot", "text": reply, "ts": datetime.now(timezone.utc).isoformat(), "intent": intent})
    session.update({
        "messages": msgs[-20:],
        "last_intent": intent,
        "updated_at": datetime.now(timezone.utc).isoformat(),
    })
    await repo.upsert_session(session)

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
