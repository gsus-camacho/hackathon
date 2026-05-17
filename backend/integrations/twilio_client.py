"""Twilio WhatsApp messaging client."""
import os
import logging
from typing import Optional, Dict
from twilio.rest import Client

logger = logging.getLogger(__name__)

_client: Optional[Client] = None


def get_client() -> Client:
    global _client
    if _client is None:
        _client = Client(
            os.environ["TWILIO_ACCOUNT_SID"],
            os.environ["TWILIO_AUTH_TOKEN"],
        )
    return _client


def send_whatsapp_text(to: str, body: str) -> Dict:
    """Send free-form WhatsApp text (must be within 24h session window)."""
    client = get_client()
    to_addr = to if to.startswith("whatsapp:") else f"whatsapp:{to}"
    msg = client.messages.create(
        from_=os.environ["TWILIO_WHATSAPP_FROM"],
        to=to_addr,
        body=body,
    )
    logger.info("Sent WhatsApp text sid=%s to=%s", msg.sid, to_addr)
    return {"sid": msg.sid, "status": msg.status, "to": to_addr}


def send_whatsapp_template(to: str, content_sid: str, variables: Dict[str, str]) -> Dict:
    """Send a Twilio template (contentSid) with variables. Use for outbound notifications."""
    import json
    client = get_client()
    to_addr = to if to.startswith("whatsapp:") else f"whatsapp:{to}"
    msg = client.messages.create(
        from_=os.environ["TWILIO_WHATSAPP_FROM"],
        to=to_addr,
        content_sid=content_sid,
        content_variables=json.dumps(variables),
    )
    logger.info("Sent WhatsApp template sid=%s to=%s", msg.sid, to_addr)
    return {"sid": msg.sid, "status": msg.status, "to": to_addr}
