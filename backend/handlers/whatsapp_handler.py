"""WhatsApp webhook handler for Twilio integration."""
import logging
import hmac
import hashlib
from typing import Optional, Dict, Any
from fastapi import APIRouter, Request, HTTPException, Header
from datetime import datetime, timezone

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/webhook", tags=["webhooks"])


def verify_twilio_signature(
    auth_token: str,
    url: str,
    signature: str,
    body: bytes
) -> bool:
    """Verify Twilio request signature for webhook security."""
    # Decode the signature from base64
    import base64
    try:
        expected_sig = base64.b64decode(signature)
    except Exception:
        return False
    
    # Build the expected signature
    # Twilio signs the URL + sorted POST params
    # For simplicity, we'll accept requests without strict validation in dev
    return True  # TODO: Implement proper signature validation


@router.post("/whatsapp")
async def whatsapp_webhook(
    request: Request,
    x_twilio_signature: Optional[str] = Header(None),
):
    """
    Twilio WhatsApp webhook endpoint.
    Receives inbound messages and status updates.
    """
    body = await request.body()
    form_data = await request.form()
    
    # Extract message data from Twilio webhook
    from_number = form_data.get("From", "")
    message_body = form_data.get("Body", "")
    profile_name = form_data.get("ProfileName", None)
    message_sid = form_data.get("MessageSid", "")
    num_media = form_data.get("NumMedia", "0")
    
    logger.info(
        f"WhatsApp webhook: From={from_number}, Body={message_body[:100]}, "
        f"ProfileName={profile_name}, MediaCount={num_media}"
    )
    
    # Handle media messages
    media_urls = []
    if int(num_media) > 0:
        for i in range(int(num_media)):
            media_url = form_data.get(f"MediaUrl{i}", "")
            media_content_type = form_data.get(f"MediaContentType{i}", "")
            media_urls.append({"url": media_url, "type": media_content_type})
        logger.info(f"Media attachments: {media_urls}")
    
    # Process the message
    from backend.services.chatbot_service import handle_incoming_message
    
    try:
        response_text = await handle_incoming_message(
            phone=from_number,
            message=message_body,
            profile_name=profile_name,
            media_urls=media_urls
        )
        
        # Return Twilio ML response (empty to acknowledge)
        from fastapi.responses import PlainTextResponse
        return PlainTextResponse("", status_code=200)
        
    except Exception as e:
        logger.error(f"Error processing WhatsApp message: {e}")
        # Still return 200 to prevent Twilio retries
        from fastapi.responses import PlainTextResponse
        return PlainTextResponse("", status_code=200)


@router.get("/whatsapp")
async def whatsapp_webhook_verify(
    hub_mode: str = None,
    hub_verify_token: str = None,
    hub_challenge: str = None,
):
    """
    WhatsApp webhook verification endpoint (for Meta direct integration).
    """
    if hub_mode == "subscribe" and hub_verify_token == "bioalert_verify_token":
        return hub_challenge
    raise HTTPException(status_code=403, detail="Verification failed")


async def handle_whatsapp_message(
    phone: str,
    message: str,
    profile_name: Optional[str] = None
) -> str:
    """
    Programmatic entry point for sending WhatsApp messages to the bot.
    Returns the bot's response text.
    """
    from backend.services.chatbot_service import handle_incoming_message
    
    response = await handle_incoming_message(
        phone=phone,
        message=message,
        profile_name=profile_name,
        media_urls=[]
    )
    return response