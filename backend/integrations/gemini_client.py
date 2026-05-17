"""Gemini 3 Flash via Emergent LLM key."""
import os
import json
import logging
from typing import Optional, Dict, Any
from emergentintegrations.llm.chat import LlmChat, UserMessage

logger = logging.getLogger(__name__)

EMERGENT_KEY = os.environ["EMERGENT_LLM_KEY"]
MODEL = os.environ.get("GEMINI_MODEL", "gemini-3-flash-preview")


def _build_chat(session_id: str, system_message: str) -> LlmChat:
    return LlmChat(
        api_key=EMERGENT_KEY,
        session_id=session_id,
        system_message=system_message,
    ).with_model("gemini", MODEL)


async def chat_send(session_id: str, system_message: str, user_text: str) -> str:
    """Send a single user message and return the assistant reply."""
    chat = _build_chat(session_id, system_message)
    reply = await chat.send_message(UserMessage(text=user_text))
    return reply if isinstance(reply, str) else str(reply)


async def chat_json(session_id: str, system_message: str, user_text: str) -> Dict[str, Any]:
    """Ask Gemini to return strict JSON. Parses the response."""
    sys_msg = system_message + "\n\nResponde EXCLUSIVAMENTE con JSON válido, sin texto adicional."
    raw = await chat_send(session_id, sys_msg, user_text)
    # Try to extract JSON from possible markdown fences
    text = raw.strip()
    if text.startswith("```"):
        text = text.strip("`")
        if text.lower().startswith("json"):
            text = text[4:]
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        # Find first { ... last }
        start = text.find("{")
        end = text.rfind("}")
        if start >= 0 and end > start:
            return json.loads(text[start : end + 1])
        logger.error("Gemini did not return JSON: %s", raw[:200])
        return {}
