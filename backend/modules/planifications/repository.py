"""Planifications repository: balance + weekly meal plans."""
from typing import Optional, List, Dict
from core.postgres import fetch_all, fetch_one
from core.sqlite import get_db


# -- Balance queries (PostgreSQL) --

async def get_student_balance(usuario_identificacion: str) -> Optional[Dict]:
    q = """
        WITH r AS (
          SELECT COALESCE(SUM(valor), 0) AS total, MAX(fecha) AS last_date
          FROM hackaton_recargas WHERE usuario_identificacion=$1
        ),
        v AS (
          SELECT COALESCE(SUM(CAST(precio AS NUMERIC) * CAST(cantidad AS INT)), 0) AS total,
                 MAX(fecha::date) AS last_date
          FROM hackaton_ventas WHERE usuario_identificacion=$1
        ),
        info AS (
          SELECT nombre_estudiante, nit_colegio FROM hackaton_ventas
          WHERE usuario_identificacion=$1 LIMIT 1
        )
        SELECT
          (SELECT total FROM r) AS total_recargas,
          (SELECT total FROM v) AS total_consumo,
          (SELECT last_date FROM r) AS last_recharge,
          (SELECT last_date FROM v) AS last_consumption,
          (SELECT nombre_estudiante FROM info) AS nombre_estudiante,
          (SELECT nit_colegio FROM info) AS nit_colegio
    """
    return await fetch_one(q, usuario_identificacion)


async def list_students_at_risk_fast(nit_colegio: Optional[str] = None, limit: int = 50) -> List[Dict]:
    if nit_colegio:
        q = """
            SELECT v.usuario_identificacion,
                   MAX(v.nombre_estudiante) AS nombre_estudiante,
                   MAX(v.nit_colegio) AS nit_colegio,
                   MAX(v.fecha::date) AS last_consumption
            FROM hackaton_ventas v
            WHERE v.nit_colegio=$1 AND v.fecha::date >= CURRENT_DATE - 14
              AND NOT EXISTS (
                SELECT 1 FROM hackaton_recargas r
                WHERE r.usuario_identificacion = v.usuario_identificacion
                  AND r.fecha >= CURRENT_DATE - 30
              )
            GROUP BY v.usuario_identificacion
            ORDER BY last_consumption DESC LIMIT $2
        """
        rows = await fetch_all(q, nit_colegio, limit)
    else:
        q = """
            SELECT v.usuario_identificacion,
                   MAX(v.nombre_estudiante) AS nombre_estudiante,
                   MAX(v.nit_colegio) AS nit_colegio,
                   MAX(v.fecha::date) AS last_consumption
            FROM hackaton_ventas v
            WHERE v.fecha::date >= CURRENT_DATE - 14
              AND NOT EXISTS (
                SELECT 1 FROM hackaton_recargas r
                WHERE r.usuario_identificacion = v.usuario_identificacion
                  AND r.fecha >= CURRENT_DATE - 30
              )
            GROUP BY v.usuario_identificacion
            ORDER BY last_consumption DESC LIMIT $1
        """
        rows = await fetch_all(q, limit)
    enriched = []
    for r in rows:
        uid = r["usuario_identificacion"]
        consumo = await fetch_one(
            "SELECT COALESCE(SUM(CAST(precio AS NUMERIC) * CAST(cantidad AS INT)), 0) AS total FROM hackaton_ventas WHERE usuario_identificacion=$1",
            uid,
        )
        recargas = await fetch_one(
            "SELECT COALESCE(SUM(valor), 0) AS total, MAX(fecha) AS last_recharge FROM hackaton_recargas WHERE usuario_identificacion=$1",
            uid,
        )
        enriched.append({
            **r,
            "total_consumo": float(consumo["total"]) if consumo else 0.0,
            "total_recargas": float(recargas["total"]) if recargas else 0.0,
            "last_recharge": recargas.get("last_recharge") if recargas else None,
        })
    return enriched


async def count_students_at_risk(nit_colegio: Optional[str] = None) -> int:
    if nit_colegio:
        q = """
            SELECT COUNT(DISTINCT v.usuario_identificacion) AS c
            FROM hackaton_ventas v
            WHERE v.nit_colegio = $1
              AND v.fecha::date >= CURRENT_DATE - 14
              AND NOT EXISTS (
                SELECT 1 FROM hackaton_recargas r
                WHERE r.usuario_identificacion = v.usuario_identificacion
                  AND r.fecha >= CURRENT_DATE - 30
              )
        """
        row = await fetch_one(q, nit_colegio)
    else:
        q = """
            SELECT COUNT(DISTINCT v.usuario_identificacion) AS c
            FROM hackaton_ventas v
            WHERE v.fecha::date >= CURRENT_DATE - 14
              AND NOT EXISTS (
                SELECT 1 FROM hackaton_recargas r
                WHERE r.usuario_identificacion = v.usuario_identificacion
                  AND r.fecha >= CURRENT_DATE - 30
              )
        """
        row = await fetch_one(q)
    return int(row["c"]) if row else 0


async def search_students(query: str, limit: int = 20) -> List[Dict]:
    q = """
        SELECT DISTINCT usuario_identificacion, nombre_estudiante, nit_colegio, colegio
        FROM hackaton_ventas
        WHERE LOWER(nombre_estudiante) LIKE LOWER($1) OR usuario_identificacion LIKE $1
        LIMIT $2
    """
    return await fetch_all(q, f"%{query}%", limit)


async def get_parent_students(identificacion_padre: str) -> List[Dict]:
    q = """
        SELECT DISTINCT usuario_identificacion, nombre_estudiante, nit_colegio, colegio
        FROM hackaton_ventas WHERE identificacion_padre=$1
    """
    return await fetch_all(q, identificacion_padre)


# -- Weekly meal plans (MongoDB) --

async def insert_meal_plan(doc: Dict) -> Dict:
    await get_db().meal_plans.insert_one({**doc})
    return doc


async def list_meal_plans(hijo_id: Optional[str] = None, limit: int = 50) -> List[Dict]:
    q: Dict = {}
    if hijo_id:
        q["hijo_id"] = hijo_id
    return await get_db().meal_plans.find(q, {"_id": 0}).sort("week_start", -1).to_list(limit)


async def get_meal_plan(plan_id: str) -> Optional[Dict]:
    return await get_db().meal_plans.find_one({"id": plan_id}, {"_id": 0})


async def get_active_plan_for_hijo(hijo_id: str) -> Optional[Dict]:
    return await get_db().meal_plans.find_one(
        {"hijo_id": hijo_id}, {"_id": 0}, sort=[("week_start", -1)]
    )


async def update_meal_plan(plan_id: str, updates: Dict) -> Optional[Dict]:
    await get_db().meal_plans.update_one({"id": plan_id}, {"$set": updates})
    return await get_meal_plan(plan_id)


async def delete_meal_plan(plan_id: str) -> bool:
    res = await get_db().meal_plans.delete_one({"id": plan_id})
    return res.deleted_count > 0
