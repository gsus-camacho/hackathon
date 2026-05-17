"""Discounts repository: package CRUD in Mongo + product analysis from PG."""
from typing import Optional, List, Dict
from core.mongo import get_db
from core.postgres import fetch_all


async def insert_package(doc: Dict) -> Dict:
    await get_db().packages.insert_one({**doc})
    return doc


async def list_packages(nit_colegio: Optional[str] = None, limit: int = 50) -> List[Dict]:
    q = {"active": True}
    if nit_colegio:
        q["$or"] = [{"nit_colegio": nit_colegio}, {"nit_colegio": None}]
    return await get_db().packages.find(q, {"_id": 0}).sort("created_at", -1).to_list(limit)


async def get_package(package_id: str) -> Optional[Dict]:
    return await get_db().packages.find_one({"id": package_id}, {"_id": 0})


async def deactivate_package(package_id: str) -> bool:
    res = await get_db().packages.update_one({"id": package_id}, {"$set": {"active": False}})
    return res.modified_count > 0


async def get_top_combos(nit_colegio: Optional[str], limit: int = 5) -> List[Dict]:
    """Top products grouped to inspire a bundle."""
    if nit_colegio:
        q = """
            SELECT nombre_producto AS name,
                   COUNT(*) AS purchases,
                   AVG(CAST(precio AS NUMERIC)) AS avg_price,
                   SUM(CAST(cantidad AS INT)) AS units
            FROM hackaton_ventas WHERE nit_colegio=$1
            GROUP BY nombre_producto ORDER BY purchases DESC LIMIT $2
        """
        rows = await fetch_all(q, nit_colegio, limit)
    else:
        q = """
            SELECT nombre_producto AS name,
                   COUNT(*) AS purchases,
                   AVG(CAST(precio AS NUMERIC)) AS avg_price,
                   SUM(CAST(cantidad AS INT)) AS units
            FROM hackaton_ventas
            GROUP BY nombre_producto ORDER BY purchases DESC LIMIT $1
        """
        rows = await fetch_all(q, limit)
    return [
        {
            "name": r["name"],
            "purchases": int(r["purchases"]),
            "avg_price": float(r["avg_price"] or 0),
            "units": int(r["units"] or 0),
        }
        for r in rows
    ]


async def avg_recharge_amount(nit_colegio: Optional[str] = None) -> float:
    if nit_colegio:
        rows = await fetch_all(
            "SELECT AVG(valor) AS avg FROM hackaton_recargas WHERE nit_colegio=$1", nit_colegio
        )
    else:
        rows = await fetch_all("SELECT AVG(valor) AS avg FROM hackaton_recargas")
    if rows and rows[0].get("avg"):
        return float(rows[0]["avg"])
    return 0.0
