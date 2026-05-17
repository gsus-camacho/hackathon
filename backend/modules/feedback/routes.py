"""Feedback API routes (👍👎 product voting)."""
from fastapi import APIRouter, HTTPException
from typing import Optional
from modules.feedback import service as svc
from modules.feedback.schemas import VoteCreate
from modules.feedback.errors import InvalidRatingError

router = APIRouter(prefix="/feedback", tags=["feedback"])


@router.post("/vote")
async def vote(req: VoteCreate):
    try:
        return await svc.vote(req)
    except InvalidRatingError as e:
        raise HTTPException(400, str(e))


@router.get("/votes")
async def list_votes(product_name: Optional[str] = None, limit: int = 100):
    return await svc.list_votes(product_name, limit)


@router.get("/products")
async def per_product(nit_colegio: Optional[str] = None):
    return await svc.per_product(nit_colegio)


@router.get("/products/{product_name}")
async def product_summary(product_name: str):
    return await svc.product_summary(product_name)


@router.get("/summary")
async def summary(nit_colegio: Optional[str] = None):
    return await svc.summary(nit_colegio)
