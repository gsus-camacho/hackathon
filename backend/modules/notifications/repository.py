"""Notifications repository: stores Twilio messages + bot sessions in MongoDB."""
from typing import Optional, List, Dict
from datetime import datetime, timezone
from core.mongo import get_db


async def insert_notification(doc: Dict) -> Dict:
    await get_db().notifications.insert_one({**doc})
    return doc


async def list_notifications(limit: int = 50, kind: Optional[str] = None) -> List[Dict]:
    q = {}
    if kind:
        q["kind"] = kind
    return await get_db().notifications.find(q, {"_id": 0}).sort("created_at", -1).to_list(limit)


async def count_today() -> int:
    today = datetime.now(timezone.utc).date().isoformat()
    return await get_db().notifications.count_documents({"created_at": {"$gte": today}})


async def get_session_by_phone(phone: str) -> Optional[Dict]:
    return await get_db().bot_sessions.find_one({"phone": phone}, {"_id": 0})


async def upsert_session(session: Dict) -> None:
    await get_db().bot_sessions.update_one(
        {"phone": session["phone"]},
        {"$set": session},
        upsert=True,
    )


async def list_sessions(limit: int = 50) -> List[Dict]:
    return await get_db().bot_sessions.find({}, {"_id": 0}).sort("updated_at", -1).to_list(limit)


async def count_sessions_today() -> int:
    today = datetime.now(timezone.utc).date().isoformat()
    return await get_db().bot_sessions.count_documents({"updated_at": {"$gte": today}})
