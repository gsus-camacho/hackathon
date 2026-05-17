"""Bot API routes - WhatsApp chatbot endpoints."""
import logging
from typing import Optional, Dict, Any
from fastapi import APIRouter, HTTPException, BackgroundTasks
from pydantic import BaseModel, Field

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/bot", tags=["chatbot"])


class ChatMessage(BaseModel):
    """Request model for chat messages."""
    phone: str = Field(..., description="WhatsApp phone number")
    message: str = Field(..., description="User message text")
    profile_name: Optional[str] = Field(None, description="User's WhatsApp profile name")


class ChatResponse(BaseModel):
    """Response model for chat messages."""
    success: bool
    response: str
    intent: Optional[str] = None
    session_id: Optional[str] = None


@router.post("/message", response_model=ChatResponse)
async def send_chat_message(req: ChatMessage):
    """
    Send a message to the WhatsApp bot and get a response.
    This endpoint simulates receiving a WhatsApp message.
    
    Use this for testing or when integrating with a custom WhatsApp UI.
    """
    try:
        from backend.services.chatbot_service import handle_incoming_message
        
        response_text = await handle_incoming_message(
            phone=req.phone,
            message=req.message,
            profile_name=req.profile_name,
            media_urls=None
        )
        
        # Get session info
        from backend.services.conversation_memory import get_conversation_memory
        memory = get_conversation_memory()
        session = await memory.get_session(req.phone)
        
        return ChatResponse(
            success=True,
            response=response_text,
            intent=session.get("last_intent") if session else None,
            session_id=session.get("id") if session else None
        )
        
    except Exception as e:
        logger.error(f"Error processing chat message: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/session/{phone}")
async def get_session_info(phone: str):
    """
    Get conversation session info for a phone number.
    """
    from backend.services.conversation_memory import get_conversation_memory
    
    memory = get_conversation_memory()
    session = await memory.get_session(phone)
    
    if not session:
        return {"exists": False, "phone": phone}
    
    return {
        "exists": True,
        "session_id": session.get("id"),
        "phone": session.get("phone"),
        "identificacion_padre": session.get("identificacion_padre"),
        "last_intent": session.get("last_intent"),
        "message_count": len(session.get("messages", [])),
        "created_at": session.get("created_at"),
        "updated_at": session.get("updated_at"),
    }


@router.delete("/session/{phone}")
async def delete_session(phone: str):
    """
    Delete a conversation session.
    """
    from backend.services.conversation_memory import get_conversation_memory
    
    memory = get_conversation_memory()
    deleted = await memory.delete_session(phone)
    
    return {"deleted": deleted, "phone": phone}


@router.get("/sessions")
async def list_sessions(limit: int = 50):
    """
    List recent conversation sessions.
    """
    from backend.services.conversation_memory import get_conversation_memory
    
    memory = get_conversation_memory()
    sessions = await memory.get_recent_sessions(limit)
    
    return {"sessions": sessions, "count": len(sessions)}


@router.post("/simulate/{phone}")
async def simulate_conversation(phone: str, scenario: str = "greeting"):
    """
    Simulate a conversation scenario for testing.
    
    Scenarios:
    - greeting: Simple greeting
    - consumption: Ask about what student ate
    - balance: Ask about balance
    - package: Ask about packages
    - alerts: Ask about alerts
    """
    from backend.services.chatbot_service import handle_incoming_message
    
    scenarios = {
        "greeting": "Hola, ¿cómo estás?",
        "consumption": "¿Qué comió Juan hoy?",
        "balance": "¿Cuándo se acaba mi saldo?",
        "package": "Quiero comprar un paquete",
        "alerts": "¿Hay alertas de alergenos?",
        "unknown": "¿Qué tiempo hace hoy?",
    }
    
    message = scenarios.get(scenario, scenarios["greeting"])
    
    response_text = await handle_incoming_message(
        phone=phone,
        message=message,
        profile_name="Test User",
        media_urls=None
    )
    
    return {
        "scenario": scenario,
        "sent_message": message,
        "bot_response": response_text,
        "phone": phone
    }


@router.get("/intents")
async def list_intents():
    """
    List available bot intents and their descriptions.
    """
    return {
        "intents": [
            {
                "name": "consumption",
                "description": "El padre pregunta qué compró su hijo, qué consumió, qué comió",
                "examples": ["¿Qué comió Juan hoy?", "¿Qué compró mi hijo?", "¿Consumió algo?"]
            },
            {
                "name": "balance",
                "description": "Pregunta sobre saldo, dinero, recarga, cuándo se acaba",
                "examples": ["¿Cuánto saldo me queda?", "¿Cuándo se acaba el dinero?", "Necesito recargar"]
            },
            {
                "name": "package",
                "description": "Pregunta por paquetes, ofertas, descuentos, combos",
                "examples": ["Quiero un paquete", "¿Qué paquetes hay?", "Ofertas disponibles"]
            },
            {
                "name": "alerts",
                "description": "Alergenos, alertas, seguridad, reportar problema",
                "examples": ["¿Hay alertas?", "Mi hijo es alérgico", "Reportar problema"]
            },
            {
                "name": "greeting",
                "description": "Saludo o conversación social",
                "examples": ["Hola", "Buenos días", "Gracias"]
            },
            {
                "name": "unknown",
                "description": "Cualquier otra cosa que no encaje",
                "examples": ["¿Qué tiempo hace?", "Cuéntame un chiste"]
            }
        ]
    }