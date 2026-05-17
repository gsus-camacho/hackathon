"""Feedback repository: ratings in MongoDB."""
from typing import Optional, List, Dict
from core.mongo import get_db


async def insert_rating(doc: Dict) -> Dict:
    await get_db().ratings.insert_one({**doc})
    return doc


async def list_ratings(nit_colegio: Optional[str] = None, limit: int = 50) -> List[Dict]:
    q = {}
    if nit_colegio:
        q["nit_colegio"] = nit_colegio
    return await get_db().ratings.find(q, {"_id": 0}).sort("created_at", -1).to_list(limit)


async def average_rating(nit_colegio: Optional[str] = None) -> float:
    q = {}
    if nit_colegio:
        q["nit_colegio"] = nit_colegio
    pipeline = [{"$match": q}, {"$group": {"_id": None, "avg": {"$avg": "$score"}}}]
    cursor = get_db().ratings.aggregate(pipeline)
    async for row in cursor:
        return float(row.get("avg") or 0)
    return 0.0


async def count_ratings(nit_colegio: Optional[str] = None) -> int:
    q = {}
    if nit_colegio:
        q["nit_colegio"] = nit_colegio
    return await get_db().ratings.count_documents(q)
