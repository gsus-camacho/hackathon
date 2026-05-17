"""Recommendations repository: stores AI recommendations + allergens in MongoDB."""
from typing import Optional, List, Dict
from core.sqlite import get_db


async def insert_recommendation(doc: Dict) -> Dict:
    await get_db().recommendations.insert_one({**doc})
    return doc


async def list_recommendations(nit_colegio: Optional[str] = None, limit: int = 20) -> List[Dict]:
    q = {}
    if nit_colegio:
        q["$or"] = [{"nit_colegio": nit_colegio}, {"nit_colegio": None}]
    return await get_db().recommendations.find(q, {"_id": 0}).sort("created_at", -1).to_list(limit)


async def insert_allergen(doc: Dict) -> Dict:
    await get_db().allergens.insert_one({**doc})
    return doc


async def list_allergens(nit_colegio: Optional[str] = None, limit: int = 200) -> List[Dict]:
    q = {}
    if nit_colegio:
        q["nit_colegio"] = nit_colegio
    return await get_db().allergens.find(q, {"_id": 0}).sort("created_at", -1).to_list(limit)


async def get_allergens_for_student(usuario_identificacion: str) -> List[str]:
    doc = await get_db().allergens.find_one(
        {"usuario_identificacion": usuario_identificacion}, {"_id": 0}
    )
    return doc.get("allergens", []) if doc else []


async def count_allergens(nit_colegio: Optional[str] = None) -> int:
    q = {}
    if nit_colegio:
        q["nit_colegio"] = nit_colegio
    return await get_db().allergens.count_documents(q)
