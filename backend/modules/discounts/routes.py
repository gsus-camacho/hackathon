"""Discounts API routes."""
from fastapi import APIRouter, HTTPException
from typing import Optional
from modules.discounts import service as svc
from modules.discounts.schemas import PackageCreate
from modules.discounts.errors import InvalidPackageError

router = APIRouter(prefix="/discounts", tags=["discounts"])


@router.get("/packages")
async def list_packages(nit_colegio: Optional[str] = None):
    return await svc.list_packages(nit_colegio)


@router.post("/packages")
async def create_package(req: PackageCreate):
    try:
        return await svc.create_package(req)
    except InvalidPackageError as e:
        raise HTTPException(400, str(e))


@router.post("/packages/generate")
async def generate(nit_colegio: Optional[str] = None):
    return await svc.generate_and_save(nit_colegio)


@router.delete("/packages/{package_id}")
async def deactivate(package_id: str):
    ok = await svc.deactivate(package_id)
    if not ok:
        raise HTTPException(404, "Paquete no encontrado")
    return {"status": "deactivated"}


@router.get("/recharge-suggestion")
async def suggest_recharge(nit_colegio: Optional[str] = None):
    return {"suggested_amount": await svc.suggested_recharge(nit_colegio)}
