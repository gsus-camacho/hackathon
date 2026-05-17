"""Gemini 3 Flash integration stub for local backend startup."""
import logging
from typing import Dict, Any

logger = logging.getLogger(__name__)

async def chat_send(session_id: str, system_message: str, user_text: str) -> str:
    """Return a stable stub response for startup and local testing."""
    logger.debug("chat_send stub called: %s", user_text)
    return (
        "Respuesta simulada de Gemini. "
        "Este backend funciona con SQLite y no requiere la librería emergentintegrations."
    )

async def chat_json(session_id: str, system_message: str, user_text: str) -> Dict[str, Any]:
    """Return a stable JSON stub response for startup and local testing."""
    logger.debug("chat_json stub called: %s", user_text)
    return {
        "result": "simulado",
        "input": user_text,
        "message": "Este es un resultado de prueba."
    }
