"""Feedback repository: stores product thumb votes in MongoDB."""
from typing import Optional, List, Dict
from core.mongo import get_db


async def insert_vote(doc: Dict) -> Dict:
    await get_db().product_votes.insert_one({**doc})
    return doc


async def list_votes(product_name: Optional[str] = None, limit: int = 200) -> List[Dict]:
    q: Dict = {}
    if product_name:
        q["product_name"] = product_name
    return await get_db().product_votes.find(q, {"_id": 0}).sort("created_at", -1).to_list(limit)


async def aggregate_per_product(nit_colegio: Optional[str] = None) -> List[Dict]:
    match: Dict = {}
    if nit_colegio:
        match["nit_colegio"] = nit_colegio
    pipeline = [
        {"$match": match} if match else {"$match": {}},
        {
            "$group": {
                "_id": "$product_name",
                "up": {"$sum": {"$cond": [{"$eq": ["$vote", "up"]}, 1, 0]}},
                "down": {"$sum": {"$cond": [{"$eq": ["$vote", "down"]}, 1, 0]}},
            }
        },
        {"$sort": {"up": -1}},
    ]
    out = []
    async for r in get_db().product_votes.aggregate(pipeline):
        up = int(r.get("up", 0))
        down = int(r.get("down", 0))
        total = up + down
        out.append({
            "product_name": r.get("_id") or "",
            "up": up,
            "down": down,
            "total": total,
            "score_pct": round((up / total * 100) if total else 0, 1),
        })
    return out


async def get_product_summary(product_name: str) -> Dict:
    pipeline = [
        {"$match": {"product_name": product_name}},
        {
            "$group": {
                "_id": "$product_name",
                "up": {"$sum": {"$cond": [{"$eq": ["$vote", "up"]}, 1, 0]}},
                "down": {"$sum": {"$cond": [{"$eq": ["$vote", "down"]}, 1, 0]}},
            }
        },
    ]
    async for r in get_db().product_votes.aggregate(pipeline):
        up, down = int(r.get("up", 0)), int(r.get("down", 0))
        total = up + down
        return {
            "product_name": product_name,
            "up": up,
            "down": down,
            "total": total,
            "score_pct": round((up / total * 100) if total else 0, 1),
        }
    return {"product_name": product_name, "up": 0, "down": 0, "total": 0, "score_pct": 0}
