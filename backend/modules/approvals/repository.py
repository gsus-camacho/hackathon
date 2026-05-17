"""Product approvals persistence."""
from typing import Optional, List, Dict
from datetime import datetime, timezone
from core.sqlite import get_db


async def insert(doc: Dict) -> Dict:
    await get_db().product_approvals.insert_one({**doc})
    return doc


async def get(approval_id: str) -> Optional[Dict]:
    return await get_db().product_approvals.find_one({"id": approval_id}, {"_id": 0})


async def update(approval_id: str, updates: Dict) -> Optional[Dict]:
    await get_db().product_approvals.update_one({"id": approval_id}, {"$set": updates})
    return await get(approval_id)


async def list_pending(
    identificacion_padre: Optional[str] = None,
    nit_colegio: Optional[str] = None,
    limit: int = 100,
) -> List[Dict]:
    q: Dict = {"status": "pending"}
    if identificacion_padre:
        q["identificacion_padre"] = identificacion_padre
    if nit_colegio:
        q["nit_colegio"] = nit_colegio
    return await get_db().product_approvals.find(q, {"_id": 0}).sort("created_at", -1).to_list(limit)


async def find_latest_pending_for_parent(identificacion_padre: str) -> Optional[Dict]:
    rows = await get_db().product_approvals.find(
        {"identificacion_padre": identificacion_padre, "status": "pending"},
        {"_id": 0},
    ).sort("created_at", -1).to_list(1)
    return rows[0] if rows else None


async def list_expired_pending(iso_before: str, limit: int = 50) -> List[Dict]:
    rows = await get_db().product_approvals.find({"status": "pending"}, {"_id": 0}).sort(
        "created_at", 1
    ).to_list(200)
    return [r for r in rows if (r.get("expires_at") or "") <= iso_before][:limit]


async def insert_catalog(doc: Dict) -> Dict:
    await get_db().catalog_products.insert_one({**doc})
    return doc


async def list_catalog(nit_colegio: Optional[str] = None, limit: int = 100) -> List[Dict]:
    q = {"nit_colegio": nit_colegio} if nit_colegio else {}
    return await get_db().catalog_products.find(q, {"_id": 0}).sort("created_at", -1).to_list(limit)
