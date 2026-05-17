"""Conversation memory service for WhatsApp bot sessions."""
import json
import uuid
from datetime import datetime, timezone, timedelta
from typing import Optional, Dict, List, Any
from core.sqlite import get_db


class ConversationMemory:
    """Manages conversation sessions with TTL-based cleanup."""
    
    TTL_HOURS = 1  # Session expires after 1 hour of inactivity
    MAX_MESSAGES = 20  # Keep last 20 messages in history
    
    async def get_session(self, phone: str) -> Optional[Dict[str, Any]]:
        """Retrieve session by phone number."""
        db = get_db()
        session = await db.bot_sessions.find_one({"phone": phone}, {"_id": 0})
        
        if session:
            # Check if session has expired
            updated_at = session.get("updated_at", "")
            if updated_at:
                try:
                    update_time = datetime.fromisoformat(updated_at.replace("Z", "+00:00"))
                    if datetime.now(timezone.utc) - update_time > timedelta(hours=self.TTL_HOURS):
                        await self.delete_session(phone)
                        return None
                except (ValueError, TypeError):
                    pass
            return session
        return None
    
    async def create_session(self, phone: str, identificacion_padre: Optional[str] = None) -> Dict[str, Any]:
        """Create a new conversation session."""
        session = {
            "id": str(uuid.uuid4()),
            "phone": phone,
            "identificacion_padre": identificacion_padre,
            "messages": [],
            "context": {},
            "created_at": datetime.now(timezone.utc).isoformat(),
            "updated_at": datetime.now(timezone.utc).isoformat(),
        }
        db = get_db()
        await db.bot_sessions.insert_one(session)
        return session
    
    async def update_session(
        self,
        phone: str,
        user_message: str,
        bot_response: str,
        intent: str,
        context_updates: Optional[Dict] = None
    ) -> Dict[str, Any]:
        """Update session with new message exchange."""
        session = await self.get_session(phone)
        if not session:
            # Try to identify parent from phone
            from backend.services.parent_resolver import resolve_parent_by_phone
            identificacion_padre = await resolve_parent_by_phone(phone)
            session = await self.create_session(phone, identificacion_padre)
        
        # Add messages
        now = datetime.now(timezone.utc).isoformat()
        messages = session.get("messages", [])
        messages.append({
            "role": "user",
            "text": user_message,
            "timestamp": now
        })
        messages.append({
            "role": "bot",
            "text": bot_response,
            "intent": intent,
            "timestamp": now
        })
        
        # Keep only last N messages
        messages = messages[-self.MAX_MESSAGES:]
        
        # Update context
        context = session.get("context", {})
        if context_updates:
            context.update(context_updates)
        
        # Save
        updates = {
            "messages": messages,
            "context": context,
            "last_intent": intent,
            "updated_at": now
        }
        
        db = get_db()
        await db.bot_sessions.update_one({"phone": phone}, {"$set": updates})
        
        return await self.get_session(phone)
    
    async def delete_session(self, phone: str) -> bool:
        """Delete a session."""
        db = get_db()
        result = await db.bot_sessions.delete_one({"phone": phone})
        return result.deleted_count > 0
    
    async def get_recent_sessions(self, limit: int = 50) -> List[Dict[str, Any]]:
        """Get recent sessions for admin view."""
        db = get_db()
        cursor = db.bot_sessions.find({}, {"_id": 0}).sort("updated_at", -1)
        return await cursor.to_list(limit)
    
    async def cleanup_expired_sessions(self) -> int:
        """Remove all expired sessions."""
        db = get_db()
        cutoff = (datetime.now(timezone.utc) - timedelta(hours=self.TTL_HOURS)).isoformat()
        
        # SQLite doesn't support direct JSON date comparison easily
        # So we'll fetch all and filter in Python
        all_sessions = await db.bot_sessions.find({}, {"_id": 0}).to_list(1000)
        deleted = 0
        
        for session in all_sessions:
            updated_at = session.get("updated_at", "")
            if updated_at and updated_at < cutoff:
                await db.bot_sessions.delete_one({"phone": session["phone"]})
                deleted += 1
        
        return deleted
    
    async def get_conversation_history(self, phone: str, last_n: int = 5) -> List[Dict]:
        """Get last N messages for context."""
        session = await self.get_session(phone)
        if not session:
            return []
        
        messages = session.get("messages", [])
        return messages[-last_n * 2:]  # Return pairs of user/bot messages


# Singleton instance
_conversation_memory: Optional[ConversationMemory] = None


def get_conversation_memory() -> ConversationMemory:
    """Get the singleton ConversationMemory instance."""
    global _conversation_memory
    if _conversation_memory is None:
        _conversation_memory = ConversationMemory()
    return _conversation_memory