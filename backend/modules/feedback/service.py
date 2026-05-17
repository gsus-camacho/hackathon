"""Feedback service: thumb voting + per-product aggregation."""
from typing import Optional, List, Dict
from modules.feedback import repository as repo
from modules.feedback.schemas import ProductVote, VoteCreate
from modules.feedback.errors import InvalidRatingError


async def vote(req: VoteCreate) -> Dict:
    if req.vote not in ("up", "down"):
        raise InvalidRatingError("vote must be 'up' or 'down'")
    v = ProductVote(**req.model_dump())
    doc = v.model_dump()
    await repo.insert_vote(doc)
    return doc


async def list_votes(product_name: Optional[str] = None, limit: int = 100) -> List[Dict]:
    return await repo.list_votes(product_name, limit)


async def per_product(nit_colegio: Optional[str] = None) -> List[Dict]:
    return await repo.aggregate_per_product(nit_colegio)


async def product_summary(product_name: str) -> Dict:
    return await repo.get_product_summary(product_name)


async def summary(nit_colegio: Optional[str] = None) -> Dict:
    rows = await repo.aggregate_per_product(nit_colegio)
    total_up = sum(r["up"] for r in rows)
    total_down = sum(r["down"] for r in rows)
    total = total_up + total_down
    return {
        "total_votes": total,
        "up": total_up,
        "down": total_down,
        "average_score_pct": round((total_up / total * 100) if total else 0, 1),
        "products_voted": len(rows),
    }
