"""Hijos service: child profile orchestration."""
from typing import Optional, List, Dict
from datetime import datetime, timezone
from modules.hijos import repository as repo
from modules.hijos.schemas import Hijo, HijoCreate, HijoUpdate
from modules.hijos.errors import HijoNotFoundError, DuplicateHijoError


async def create_hijo(req: HijoCreate) -> Dict:
    existing = await repo.get_by_usuario(req.usuario_identificacion)
    if existing:
        raise DuplicateHijoError(f"Ya existe un hijo con ID {req.usuario_identificacion}")
    # Try to enrich from Biofood
    enriched = await repo.lookup_student_info(req.usuario_identificacion)
    base = req.model_dump()
    if enriched:
        for k in ("nombre_estudiante", "identificacion_padre", "nombre_padre", "nit_colegio", "colegio"):
            if not base.get(k) and enriched.get(k):
                base[k] = enriched[k]
    if not base.get("nombre_estudiante"):
        base["nombre_estudiante"] = req.usuario_identificacion
    hijo = Hijo(**base)
    doc = hijo.model_dump()
    await repo.insert_hijo(doc)
    return doc


async def list_hijos(
    identificacion_padre: Optional[str] = None,
    nit_colegio: Optional[str] = None,
) -> List[Dict]:
    return await repo.list_hijos(identificacion_padre, nit_colegio)


async def get_hijo(hijo_id: str) -> Dict:
    doc = await repo.get_hijo(hijo_id)
    if not doc:
        raise HijoNotFoundError(hijo_id)
    return doc


async def update_hijo(hijo_id: str, req: HijoUpdate) -> Dict:
    updates = {k: v for k, v in req.model_dump().items() if v is not None}
    updates["updated_at"] = datetime.now(timezone.utc).isoformat()
    doc = await repo.update_hijo(hijo_id, updates)
    if not doc:
        raise HijoNotFoundError(hijo_id)
    return doc


async def delete_hijo(hijo_id: str) -> bool:
    return await repo.delete_hijo(hijo_id)
