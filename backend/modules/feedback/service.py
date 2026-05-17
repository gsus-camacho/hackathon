"""Feedback service: rating management."""
from typing import Optional, List, Dict
from modules.feedback import repository as repo
from modules.feedback.schemas import Rating, RatingCreate
from modules.feedback.errors import InvalidRatingError


async def create_rating(req: RatingCreate) -> Dict:
    if req.score < 1 or req.score > 5:
        raise InvalidRatingError("score must be between 1 and 5")
    r = Rating(**req.model_dump())
    doc = r.model_dump()
    await repo.insert_rating(doc)
    return doc


async def list_ratings(nit_colegio: Optional[str] = None, limit: int = 50) -> List[Dict]:
    return await repo.list_ratings(nit_colegio, limit)


async def summary(nit_colegio: Optional[str] = None) -> Dict:
    avg = await repo.average_rating(nit_colegio)
    total = await repo.count_ratings(nit_colegio)
    return {"average": round(avg, 2), "count": total}
