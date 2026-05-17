"""Planifications API routes."""
from fastapi import APIRouter, HTTPException
from typing import Optional
from modules.planifications import service as svc

router = APIRouter(prefix="/planifications", tags=["planifications"])


@router.get("/balance/{usuario_identificacion}")
async def balance(usuario_identificacion: str):
    pred = await svc.predict_balance(usuario_identificacion)
    if not pred:
        raise HTTPException(404, "Estudiante no encontrado")
    return pred


@router.get("/at-risk")
async def students_at_risk(nit_colegio: Optional[str] = None, limit: int = 50):
    return await svc.students_at_risk(nit_colegio, limit)


@router.get("/students/search")
async def search(q: str, limit: int = 20):
    return await svc.search_students(q, limit)
