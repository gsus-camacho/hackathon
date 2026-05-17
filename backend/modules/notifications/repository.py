"""Notifications repository: stores WhatsApp messages, bot sessions, read state in MongoDB."""
from typing import Optional, List, Dict
from datetime import datetime, timezone
from core.mongo import get_db


async def insert_notification(doc: Dict) -> Dict:
    await get_db().notifications.insert_one({**doc})
    return doc


async def list_notifications(
    limit: int = 100,
    kind: Optional[str] = None,
    read: Optional[bool] = None,
) -> List[Dict]:
    q: Dict = {}
    if kind:
        q["kind"] = kind
    if read is not None:
        q["read"] = read
    return await get_db().notifications.find(q, {"_id": 0}).sort("created_at", -1).to_list(limit)


async def mark_read(notification_id: str, read: bool = True) -> bool:
    update = {"read": read}
    if read:
        update["read_at"] = datetime.now(timezone.utc).isoformat()
    res = await get_db().notifications.update_one({"id": notification_id}, {"$set": update})
    return res.modified_count > 0


async def mark_all_read() -> int:
    res = await get_db().notifications.update_many(
        {"read": False},
        {"$set": {"read": True, "read_at": datetime.now(timezone.utc).isoformat()}},
    )
    return res.modified_count


async def count_unread() -> int:
    return await get_db().notifications.count_documents({"read": False})


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
