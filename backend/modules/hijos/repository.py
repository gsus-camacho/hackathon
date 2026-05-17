"""Hijos repository: stores configured children profiles in MongoDB."""
from typing import Optional, List, Dict
from core.sqlite import get_db
from core.postgres import fetch_one


async def insert_hijo(doc: Dict) -> Dict:
    await get_db().hijos.insert_one({**doc})
    return doc


async def list_hijos(
    identificacion_padre: Optional[str] = None,
    nit_colegio: Optional[str] = None,
    limit: int = 200,
) -> List[Dict]:
    q: Dict = {}
    if identificacion_padre:
        q["identificacion_padre"] = identificacion_padre
    if nit_colegio:
        q["nit_colegio"] = nit_colegio
    return await get_db().hijos.find(q, {"_id": 0}).sort("created_at", -1).to_list(limit)


async def get_hijo(hijo_id: str) -> Optional[Dict]:
    return await get_db().hijos.find_one({"id": hijo_id}, {"_id": 0})


async def get_by_usuario(usuario_identificacion: str) -> Optional[Dict]:
    return await get_db().hijos.find_one(
        {"usuario_identificacion": usuario_identificacion}, {"_id": 0}
    )


async def update_hijo(hijo_id: str, updates: Dict) -> Optional[Dict]:
    await get_db().hijos.update_one({"id": hijo_id}, {"$set": updates})
    return await get_hijo(hijo_id)


async def delete_hijo(hijo_id: str) -> bool:
    res = await get_db().hijos.delete_one({"id": hijo_id})
    return res.deleted_count > 0


async def lookup_student_info(usuario_identificacion: str) -> Optional[Dict]:
    """Pull student info from Biofood PostgreSQL by ID."""
    q = """
        SELECT usuario_identificacion, nombre_estudiante, identificacion_padre,
               nombre_padre, nit_colegio, colegio
        FROM hackaton_ventas
        WHERE usuario_identificacion = $1
        LIMIT 1
    """
    return await fetch_one(q, usuario_identificacion)
