"""Chatbot service - Intent detection and response generation via Gemini."""
import logging
import json
from typing import Optional, Dict, List, Any
from datetime import datetime, timezone

from integrations.gemini_client import chat_send, chat_json
from services.conversation_memory import get_conversation_memory
from services.parent_resolver import resolve_parent_by_phone, get_parent_students
from modules.planifications import service as plan_svc
from modules.discounts import service as disc_svc
from modules.recommendations import service as rec_svc
from modules.notifications import service as notif_svc
from integrations.twilio_client import send_whatsapp_text

logger = logging.getLogger(__name__)

# Intent detection prompt
INTENT_SYSTEM = """Eres BioBot, asistente de WhatsApp de BioAlert+ para padres de familia colombianos.
Clasifica el mensaje del usuario en UNA de estas intenciones:
- consumption: el padre pregunta qué compró su hijo, qué consumió, qué comió hoy o recientemente
- balance: pregunta sobre saldo, dinero, recarga, cuándo se acaba el saldo
- package: pregunta por paquetes, ofertas, descuentos, combos, comprar paquete
- alerts: alergenos, alertas, seguridad, reportar problema, algo salió mal
- greeting: saludo, hola, buenos días, gracias, conversación social
- unknown: cualquier otra cosa que no encaje

Devuelve SOLO JSON: {"intent": "consumption|balance|package|alerts|greeting|unknown", "confidence": 0.0-1.0, "entities": {"student_name": "nombre si lo mencionan"}}"""

# Response generation system prompt
REPLY_SYSTEM = """Eres BioBot, asistente cálido y profesional de BioAlert+ en WhatsApp para padres en Colombia.
- Responde en español neutro colombiano
- Máximo 5 líneas por respuesta
- Usa emojis discretos y relevantes
- Sé específico con datos cuando los tengas
- Si no tienes datos suficientes, ofrece ayudar a conseguirlos
- Formato: usa saltos de línea para legibilidad en WhatsApp"""


class ChatbotService:
    """Main chatbot service for handling WhatsApp conversations."""
    
    def __init__(self):
        self.memory = get_conversation_memory()
    
    async def detect_intent(self, message: str, context: Optional[Dict] = None) -> Dict:
        """Detect user intent from message."""
        try:
            context_str = ""
            if context:
                last_intent = context.get("last_intent", "")
                if last_intent:
                    context_str = f"Última intención: {last_intent}\n"
            
            user_prompt = f"{context_str}Mensaje del usuario: \"{message}\"\n\nClasifica la intención:"
            
            result = await chat_json(
                session_id=f"intent-{datetime.now(timezone.utc).timestamp()}",
                system_message=INTENT_SYSTEM,
                user_text=user_prompt,
            )
            
            if isinstance(result, dict):
                return result
            
            return {"intent": "unknown", "confidence": 0.5}
            
        except Exception as e:
            logger.warning(f"Intent detection failed: {e}")
            return {"intent": "unknown", "confidence": 0.0}
    
    async def _get_consumption_context(self, identificacion_padre: Optional[str]) -> str:
        """Get consumption data context for a parent's students."""
        if not identificacion_padre:
            return "(no se identificó al padre)"
        
        students = await get_parent_students(identificacion_padre)
        if not students:
            return "No encontré estudiantes vinculados."
        
        out = []
        for s in students[:3]:
            uid = s["usuario_identificacion"]
            name = s.get("nombre_estudiante", uid)
            
            # Get today's consumption
            try:
                from core.postgres import fetch_all
                today = datetime.now().date().isoformat()
                query = """
                    SELECT nombre_producto, CAST(precio AS INTEGER) as precio, 
                           CAST(cantidad AS INTEGER) as cantidad, 
                           TO_CHAR(fecha::time, 'HH24:MI') as hora
                    FROM hackaton_ventas 
                    WHERE usuario_identificacion = $1 
                      AND DATE(fecha) = $2
                    ORDER BY fecha DESC
                """
                rows = await fetch_all(query, uid, today)
                
                if rows:
                    items = []
                    total = 0
                    for row in rows:
                        items.append(f"• {row['nombre_producto']} (${row['precio']:,})")
                        total += int(row['precio']) * int(row['cantidad'])
                    
                    out.append(
                        f"{name} hoy:\n" + "\n".join(items) + 
                        f"\nTotal: ${total:,}"
                    )
                else:
                    out.append(f"{name}: Sin consumo hoy")
            except Exception as e:
                logger.warning(f"Failed to get consumption for {uid}: {e}")
                out.append(f"{name}: Error consultando consumo")
        
        return "\n\n".join(out) if out else "Sin datos de consumo."
    
    async def _get_balance_context(self, identificacion_padre: Optional[str]) -> str:
        """Get balance context for a parent's students."""
        if not identificacion_padre:
            return "(no se identificó al padre)"
        
        students = await get_parent_students(identificacion_padre)
        if not students:
            return "No encontré estudiantes vinculados."
        
        out = []
        for s in students[:3]:
            uid = s["usuario_identificacion"]
            name = s.get("nombre_estudiante", uid)
            
            bal = await plan_svc.predict_balance(uid)
            if bal:
                days = bal["days_remaining"]
                balance = bal["current_balance"]
                risk = bal["risk_level"]
                
                risk_emoji = "🔴" if risk == "high" else ("🟡" if risk == "medium" else "🟢")
                out.append(
                    f"{name}: Saldo ${balance:,.0f} | ~{days} días {risk_emoji}"
                )
            else:
                out.append(f"{name}: Sin datos de saldo")
        
        return "\n".join(out) if out else "Sin datos de saldo."
    
    async def _get_package_context(self) -> str:
        """Get available packages."""
        pkgs = await disc_svc.list_packages()
        if not pkgs:
            pkgs = await disc_svc.generate_and_save()
        
        if not pkgs:
            return "No hay paquetes disponibles."
        
        lines = []
        for p in pkgs[:4]:
            lines.append(
                f"📦 {p['name']}\n"
                f"   ${p['discounted_total']:,.0f} ({p['discount_pct']}% off)\n"
                f"   {p.get('description', '')}"
            )
        
        return "\n\n".join(lines)
    
    async def _get_alerts_context(self, identificacion_padre: Optional[str]) -> str:
        """Get allergen alerts context."""
        if not identificacion_padre:
            students = []
        else:
            students = await get_parent_students(identificacion_padre)
        
        if students:
            # Check for recent allergen risks
            alerts = []
            for s in students:
                uid = s["usuario_identificacion"]
                allergens = await rec_svc.get_allergens_for_student(uid)
                if allergens:
                    alerts.append(
                        f"⚠️ {s.get('nombre_estudiante', uid)}: "
                        f"Alergias activas: {', '.join(allergens)}"
                    )
            
            if alerts:
                return "\n".join(alerts)
        
        # General allergen info
        allergens = await rec_svc.list_allergens()
        if allergens:
            recent = allergens[:3]
            lines = [
                f"• {a.get('nombre_estudiante', 'Estudiante')}: "
                f"{', '.join(a.get('allergens', []))}"
                for a in recent
            ]
            return "Perfiles de alergia registrados:\n" + "\n".join(lines)
        
        return "No hay alertas de alergenos activas."
    
    async def generate_response(
        self,
        intent: str,
        message: str,
        context_data: str,
        conversation_history: List[Dict]
    ) -> str:
        """Generate a response based on intent and context."""
        
        history_str = ""
        if conversation_history:
            history_str = "Historial reciente:\n"
            for msg in conversation_history[-4:]:
                role = "Padre" if msg["role"] == "user" else "BioBot"
                history_str += f"{role}: {msg['text']}\n"
        
        user_prompt = (
            f"{history_str}\n"
            f"Mensaje: \"{message}\"\n"
            f"Intención: {intent}\n"
            f"Datos disponibles:\n{context_data}\n\n"
            f"Responde de manera útil y concisa:"
        )
        
        try:
            reply = await chat_send(
                session_id=f"reply-{datetime.now(timezone.utc).timestamp()}",
                system_message=REPLY_SYSTEM,
                user_text=user_prompt,
            )
            return reply
        except Exception as e:
            logger.error(f"Response generation failed: {e}")
            return self._get_fallback_response(intent)
    
    def _get_fallback_response(self, intent: str) -> str:
        """Return fallback responses when AI fails."""
        fallbacks = {
            "consumption": "🍽️ No pude consultar el consumo. Intenta de nuevo en unos minutos.",
            "balance": "💰 No pude verificar el saldo. Por favor intenta más tarde.",
            "package": "📦 Los paquetes disponibles los puedes ver en la app de BioAlert+.",
            "alerts": "⚠️ No hay alertas activas en este momento.",
            "greeting": "¡Hola! 👋 Soy BioBot. Pregúntame sobre consumo, saldo, paquetes o alertas.",
            "unknown": "Hola 👋 Soy BioBot. Puedo ayudarte con:\n• Qué comió tu hijo\n• Saldo disponible\n• Paquetes y ofertas\n• Alertas de alergenos",
        }
        return fallbacks.get(intent, "Hola 👋 ¿En qué puedo ayudarte?")
    
    async def process_message(
        self,
        phone: str,
        message: str,
        profile_name: Optional[str] = None,
        media_urls: Optional[List[Dict]] = None
    ) -> str:
        """
        Main message processing pipeline.
        Returns the bot response text.
        """
        # Handle media messages
        if media_urls and len(media_urls) > 0:
            logger.info(f"Processing media message from {phone}: {media_urls}")
            # For now, respond that we don't support media
            response = "📸 Gracias por el mensaje. Por ahora solo puedo procesar texto. ¡Escríbeme! 😊"
            await self._save_and_send(phone, message, response, "media")
            return response
        
        # Get or create session
        session = await self.memory.get_session(phone)
        if not session:
            identificacion_padre = await resolve_parent_by_phone(phone)
            session = await self.memory.create_session(phone, identificacion_padre)
        
        identificacion_padre = session.get("identificacion_padre")
        context = session.get("context", {})
        
        # Detect intent
        intent_data = await self.detect_intent(message, context)
        intent = intent_data.get("intent", "unknown")
        
        # Get context data based on intent
        if intent == "consumption":
            context_data = await self._get_consumption_context(identificacion_padre)
        elif intent == "balance":
            context_data = await self._get_balance_context(identificacion_padre)
        elif intent == "package":
            context_data = await self._get_package_context()
        elif intent == "alerts":
            context_data = await self._get_alerts_context(identificacion_padre)
        elif intent == "greeting":
            context_data = f"Padre: {profile_name or phone}\nOfrece menú de opciones."
        else:
            context_data = "No hay datos específicos. Ofrece ayuda general."
        
        # Get conversation history
        history = await self.memory.get_conversation_history(phone, last_n=3)
        
        # Generate response
        response = await self.generate_response(
            intent=intent,
            message=message,
            context_data=context_data,
            conversation_history=history
        )
        
        # Update session
        await self.memory.update_session(
            phone=phone,
            user_message=message,
            bot_response=response,
            intent=intent,
            context_updates={"profile_name": profile_name}
        )
        
        # Send WhatsApp message
        await self._save_and_send(phone, message, response, intent)
        
        return response
    
    async def _save_and_send(
        self,
        phone: str,
        user_message: str,
        bot_response: str,
        intent: str
    ):
        """Save notification and send WhatsApp message."""
        try:
            # Skip sending for test numbers
            if phone.startswith("whatsapp:test") or phone.startswith("test"):
                logger.info(f"Test number, skipping WhatsApp send: {phone}")
                return
            
            # Send via Twilio
            send_resp = send_whatsapp_text(phone, bot_response)
            
            # Save notification record
            from modules.notifications.schemas import Notification
            notif = Notification(
                kind="bot_response",
                recipient_phone=phone,
                message=bot_response,
                twilio_sid=send_resp.get("sid", ""),
                status=send_resp.get("status", "sent"),
            )
            await notif_svc.send_text.__wrapped__(notif)  # Direct insert
            
        except Exception as e:
            logger.error(f"Failed to send WhatsApp: {e}")


# Singleton instance
_chatbot_service: Optional[ChatbotService] = None


def get_chatbot_service() -> ChatbotService:
    """Get the singleton ChatbotService instance."""
    global _chatbot_service
    if _chatbot_service is None:
        _chatbot_service = ChatbotService()
    return _chatbot_service


async def handle_incoming_message(
    phone: str,
    message: str,
    profile_name: Optional[str] = None,
    media_urls: Optional[List[Dict]] = None
) -> str:
    """
    Entry point for handling incoming WhatsApp messages.
    """
    service = get_chatbot_service()
    return await service.process_message(
        phone=phone,
        message=message,
        profile_name=profile_name,
        media_urls=media_urls
    )