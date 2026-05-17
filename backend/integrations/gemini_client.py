"""Gemini 3 Flash integration stub for local backend startup."""
import logging
from typing import Dict, Any

logger = logging.getLogger(__name__)

async def chat_send(session_id: str, system_message: str, user_text: str) -> str:
    """Return a stable stub response for startup and local testing."""
    logger.debug("chat_send stub called [%s]: %s", session_id, user_text)
    if session_id.startswith("reply-"):
        return "✅ BioBot ha procesado tu solicitud. Esta es una respuesta simulada para el demo."
    if session_id.startswith("new-product-msg-"):
        return "🆕 Te contamos que el producto es nuevo y tiene buena aceptación. Revisa la nueva recomendación en el dashboard."
    return (
        "Respuesta simulada de Gemini. "
        "Este backend funciona con SQLite y no requiere la librería emergentintegrations."
    )

async def chat_json(session_id: str, system_message: str, user_text: str) -> Dict[str, Any]:
    """Return a stable JSON stub response for startup and local testing."""
    logger.debug("chat_json stub called [%s]: %s", session_id, user_text)
    lower_text = user_text.lower()
    lower_system = system_message.lower()

    if session_id.startswith("intent-") or "clasifica la intención" in lower_system:
        intent = "unknown"
        if any(k in lower_text for k in ["saldo", "recarga", "dinero", "cuánto me queda", "me queda"]):
            intent = "balance"
        elif any(k in lower_text for k in ["qué comió", "que comió", "consumió", "comió", "hoy comió"]):
            intent = "consumption"
        elif any(k in lower_text for k in ["paquete", "oferta", "combo", "descuento", "promoción"]):
            intent = "package"
        elif any(k in lower_text for k in ["alerg", "alergia", "maní", "mani", "gluten", "soya", "soja", "nuez", "marisco", "alerta"]):
            intent = "alerts"
        elif any(k in lower_text for k in ["hola", "buenos", "buenas", "gracias", "qué tal", "hey"]):
            intent = "greeting"
        return {"intent": intent, "confidence": 0.8}

    if session_id.startswith("rec-") or "genera el json" in lower_text or "recommendations" in lower_text:
        return {
            "recommendations": [
                {
                    "title": "Promueve el paquete semanal",
                    "summary": "Un 5% de descuento en paquetes semanales estabiliza recargas frecuentes y mejora la liquidez.",
                    "rationale": "Los datos muestran repetición alta en productos de la mañana; un paquete fijo reduce fricciones de recarga.",
                    "kind": "package",
                    "impact_score": 78
                },
                {
                    "title": "Alertas de alergias para nuevos productos",
                    "summary": "Detecta automáticamente productos con potencial de alérgenos y envía notificaciones tempranas a los padres.",
                    "rationale": "La seguridad alimentaria reduce riesgos operativos y mejora la confianza de las familias.",
                    "kind": "safety",
                    "impact_score": 85
                },
                {
                    "title": "Optimiza el inventario de jugos y snacks",
                    "summary": "Ajusta el surtido hacia los productos más vendidos para aumentar el ticket medio.",
                    "rationale": "Los top productos muestran un 30% de preferencia por bebidas y snacks rápidos en la mañana.",
                    "kind": "product",
                    "impact_score": 70
                }
            ]
        }

    if session_id.startswith("product-rec-") or "product recommendation" in lower_text or "recomienda" in lower_text:
        return {
            "recommendations": [
                {
                    "product": "Wrap de pollo",
                    "reason": "Es ligero, popular entre los estudiantes y complementa los snacks existentes.",
                    "category": "comida_rapida",
                    "estimated_price": 9500
                },
                {
                    "product": "Jugos naturales",
                    "reason": "Aumenta el ticket medio con una opción saludable y de bajo costo.",
                    "category": "bebida",
                    "estimated_price": 7200
                }
            ]
        }

    if session_id.startswith("package-rec-") or "package" in lower_text:
        return {
            "recommended_package": "Paquete Semanal",
            "reason": "Este paquete balancea el consumo diario con un descuento del 10% y reduce recargas frecuentes.",
            "savings": "$5.000 aprox.",
            "action": "Activa el paquete desde el dashboard o contáctanos por WhatsApp."
        }

    return {
        "result": "simulado",
        "input": user_text,
        "message": "Este es un resultado de prueba para el demo visual." 
    }
