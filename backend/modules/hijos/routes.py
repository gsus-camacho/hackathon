"""Hijos API routes."""
from fastapi import APIRouter, HTTPException
from typing import Optional
from modules.hijos import service as svc
from modules.hijos.schemas import HijoCreate, HijoUpdate
from modules.hijos.errors import HijoNotFoundError, DuplicateHijoError

router = APIRouter(prefix="/hijos", tags=["hijos"])


@router.get("/")
async def list_hijos(identificacion_padre: Optional[str] = None, nit_colegio: Optional[str] = None):
    return await svc.list_hijos(identificacion_padre, nit_colegio)


@router.post("/")
async def create_hijo(req: HijoCreate):
    try:
        return await svc.create_hijo(req)
    except DuplicateHijoError as e:
        raise HTTPException(409, str(e))


@router.get("/{hijo_id}")
async def get_hijo(hijo_id: str):
    try:
        return await svc.get_hijo(hijo_id)
    except HijoNotFoundError:
        raise HTTPException(404, "Hijo no encontrado")


@router.patch("/{hijo_id}")
async def update_hijo(hijo_id: str, req: HijoUpdate):
    try:
        return await svc.update_hijo(hijo_id, req)
    except HijoNotFoundError:
        raise HTTPException(404, "Hijo no encontrado")


@router.delete("/{hijo_id}")
async def delete_hijo(hijo_id: str):
    ok = await svc.delete_hijo(hijo_id)
    if not ok:
        raise HTTPException(404, "Hijo no encontrado")
    return {"status": "deleted"}
