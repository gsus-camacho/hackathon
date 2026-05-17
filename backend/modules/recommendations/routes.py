"""Recommendations + Allergens API routes."""
from fastapi import APIRouter, HTTPException
from typing import Optional
from modules.recommendations import service as svc
from modules.recommendations.schemas import RecommendationRequest, AllergenCreate
from modules.recommendations.errors import AIBackendError

router = APIRouter(prefix="/recommendations", tags=["recommendations"])


@router.get("/")
async def list_recommendations(nit_colegio: Optional[str] = None):
    return await svc.list_recommendations(nit_colegio)


@router.get("/personalized")
async def personalized(usuario_identificacion: str, nit_colegio: Optional[str] = None):
    return await svc.personalized_recommendations(usuario_identificacion, nit_colegio)


@router.get("/package-offer")
async def package_offer(usuario_identificacion: str, nit_colegio: Optional[str] = None):
    return await svc.package_offer(usuario_identificacion, nit_colegio)


@router.post("/generate")
async def generate(req: RecommendationRequest):
    try:
        return await svc.generate_recommendations(req)
    except AIBackendError as e:
        raise HTTPException(502, f"AI error: {e}")


# --- Allergens (lives within the recommendations module as 'safety intelligence') ---
@router.get("/allergens")
async def list_allergens(nit_colegio: Optional[str] = None):
    return await svc.list_allergens(nit_colegio)


@router.post("/allergens")
async def create_allergen(req: AllergenCreate):
    return await svc.create_allergen(req)


@router.get("/allergens/check")
async def check_allergen(usuario_identificacion: str, product_name: str):
    matched = await svc.check_allergen_risk(usuario_identificacion, product_name)
    return {"matched": matched, "risk": bool(matched)}
