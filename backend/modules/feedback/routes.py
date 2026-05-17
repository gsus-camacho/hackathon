"""Feedback API routes."""
from fastapi import APIRouter, HTTPException
from typing import Optional
from modules.feedback import service as svc
from modules.feedback.schemas import RatingCreate
from modules.feedback.errors import InvalidRatingError

router = APIRouter(prefix="/feedback", tags=["feedback"])


@router.get("/ratings")
async def list_ratings(nit_colegio: Optional[str] = None, limit: int = 50):
    return await svc.list_ratings(nit_colegio, limit)


@router.post("/ratings")
async def create_rating(req: RatingCreate):
    try:
        return await svc.create_rating(req)
    except InvalidRatingError as e:
        raise HTTPException(400, str(e))


@router.get("/summary")
async def summary(nit_colegio: Optional[str] = None):
    return await svc.summary(nit_colegio)
