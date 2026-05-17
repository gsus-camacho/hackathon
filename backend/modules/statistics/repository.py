"""Statistics repository: aggregates over Biofood PostgreSQL data."""
from typing import Optional, List, Dict
from core.postgres import fetch_all, fetch_one


async def get_schools(limit: int = 200) -> List[Dict]:
    q = """
        SELECT nit_colegio, colegio, COUNT(DISTINCT usuario_identificacion) AS total_students
        FROM hackaton_ventas
        GROUP BY nit_colegio, colegio
        ORDER BY total_students DESC
        LIMIT $1
    """
    return await fetch_all(q, limit)


async def get_school_revenue(nit_colegio: Optional[str] = None, days: int = 30) -> Dict:
    if nit_colegio:
        q = """
            SELECT
              COALESCE(SUM(CAST(precio AS NUMERIC) * CAST(cantidad AS INT)), 0) AS revenue,
              COUNT(*) AS ventas_count,
              COUNT(DISTINCT usuario_identificacion) AS students
            FROM hackaton_ventas
            WHERE nit_colegio = $1 AND fecha::date >= CURRENT_DATE - $2::int
        """
        row = await fetch_one(q, nit_colegio, days)
    else:
        q = """
            SELECT
              COALESCE(SUM(CAST(precio AS NUMERIC) * CAST(cantidad AS INT)), 0) AS revenue,
              COUNT(*) AS ventas_count,
              COUNT(DISTINCT usuario_identificacion) AS students
            FROM hackaton_ventas
            WHERE fecha::date >= CURRENT_DATE - $1::int
        """
        row = await fetch_one(q, days)
    return row or {"revenue": 0, "ventas_count": 0, "students": 0}


async def get_recargas_total(nit_colegio: Optional[str] = None, days: int = 30) -> float:
    if nit_colegio:
        q = "SELECT COALESCE(SUM(valor), 0) AS total FROM hackaton_recargas WHERE nit_colegio=$1 AND fecha >= CURRENT_DATE - $2::int"
        row = await fetch_one(q, nit_colegio, days)
    else:
        q = "SELECT COALESCE(SUM(valor), 0) AS total FROM hackaton_recargas WHERE fecha >= CURRENT_DATE - $1::int"
        row = await fetch_one(q, days)
    return float(row["total"]) if row else 0.0


async def get_top_products(nit_colegio: Optional[str] = None, limit: int = 8, days: int = 30) -> List[Dict]:
    if nit_colegio:
        q = """
            SELECT nombre_producto AS name,
                   SUM(CAST(cantidad AS INT)) AS units,
                   SUM(CAST(precio AS NUMERIC) * CAST(cantidad AS INT)) AS revenue
            FROM hackaton_ventas
            WHERE nit_colegio=$1 AND fecha::date >= CURRENT_DATE - $3::int
            GROUP BY nombre_producto
            ORDER BY revenue DESC
            LIMIT $2
        """
        rows = await fetch_all(q, nit_colegio, limit, days)
    else:
        q = """
            SELECT nombre_producto AS name,
                   SUM(CAST(cantidad AS INT)) AS units,
                   SUM(CAST(precio AS NUMERIC) * CAST(cantidad AS INT)) AS revenue
            FROM hackaton_ventas
            WHERE fecha::date >= CURRENT_DATE - $2::int
            GROUP BY nombre_producto
            ORDER BY revenue DESC
            LIMIT $1
        """
        rows = await fetch_all(q, limit, days)
    return [
        {"name": r["name"], "units": int(r["units"] or 0), "revenue": float(r["revenue"] or 0)}
        for r in rows
    ]


async def get_daily_series(nit_colegio: Optional[str] = None, days: int = 14) -> List[Dict]:
    if nit_colegio:
        ventas_q = """
            SELECT fecha::date AS d, SUM(CAST(precio AS NUMERIC) * CAST(cantidad AS INT)) AS v
            FROM hackaton_ventas
            WHERE nit_colegio=$1 AND fecha::date >= CURRENT_DATE - $2::int
            GROUP BY d ORDER BY d
        """
        ventas = await fetch_all(ventas_q, nit_colegio, days)
        recargas_q = """
            SELECT fecha AS d, SUM(valor) AS r
            FROM hackaton_recargas
            WHERE nit_colegio=$1 AND fecha >= CURRENT_DATE - $2::int
            GROUP BY d ORDER BY d
        """
        recargas = await fetch_all(recargas_q, nit_colegio, days)
    else:
        ventas_q = """
            SELECT fecha::date AS d, SUM(CAST(precio AS NUMERIC) * CAST(cantidad AS INT)) AS v
            FROM hackaton_ventas
            WHERE fecha::date >= CURRENT_DATE - $1::int
            GROUP BY d ORDER BY d
        """
        ventas = await fetch_all(ventas_q, days)
        recargas_q = """
            SELECT fecha AS d, SUM(valor) AS r
            FROM hackaton_recargas
            WHERE fecha >= CURRENT_DATE - $1::int
            GROUP BY d ORDER BY d
        """
        recargas = await fetch_all(recargas_q, days)
    by_date: Dict[str, Dict[str, float]] = {}
    for row in ventas:
        d = row["d"].isoformat() if hasattr(row["d"], "isoformat") else str(row["d"])
        by_date.setdefault(d, {"ventas": 0.0, "recargas": 0.0})
        by_date[d]["ventas"] = float(row["v"] or 0)
    for row in recargas:
        d = row["d"].isoformat() if hasattr(row["d"], "isoformat") else str(row["d"])
        by_date.setdefault(d, {"ventas": 0.0, "recargas": 0.0})
        by_date[d]["recargas"] = float(row["r"] or 0)
    return [
        {"date": d, "ventas": v["ventas"], "recargas": v["recargas"]}
        for d, v in sorted(by_date.items())
    ]


async def get_network_avg_revenue_per_student(days: int = 30) -> float:
    q = """
        SELECT COALESCE(SUM(CAST(precio AS NUMERIC) * CAST(cantidad AS INT)), 0) /
               NULLIF(COUNT(DISTINCT usuario_identificacion), 0) AS avg_per_student
        FROM hackaton_ventas
        WHERE fecha::date >= CURRENT_DATE - $1::int
    """
    row = await fetch_one(q, days)
    return float(row["avg_per_student"] or 0) if row else 0.0


async def get_school_avg_revenue_per_student(nit_colegio: str, days: int = 30) -> float:
    q = """
        SELECT COALESCE(SUM(CAST(precio AS NUMERIC) * CAST(cantidad AS INT)), 0) /
               NULLIF(COUNT(DISTINCT usuario_identificacion), 0) AS avg_per_student
        FROM hackaton_ventas
        WHERE nit_colegio=$1 AND fecha::date >= CURRENT_DATE - $2::int
    """
    row = await fetch_one(q, nit_colegio, days)
    return float(row["avg_per_student"] or 0) if row else 0.0


async def get_recent_activity(nit_colegio: Optional[str] = None, limit: int = 12) -> List[Dict]:
    if nit_colegio:
        ventas_q = """
            SELECT 'venta' AS kind, fecha AS ts, nombre_estudiante, nombre_producto,
                   (CAST(precio AS NUMERIC) * CAST(cantidad AS INT)) AS amount
            FROM hackaton_ventas WHERE nit_colegio=$1
            ORDER BY fecha DESC LIMIT $2
        """
        recargas_q = """
            SELECT 'recarga' AS kind, fecha::text AS ts, nombre_estudiante, NULL AS nombre_producto, valor AS amount
            FROM hackaton_recargas WHERE nit_colegio=$1
            ORDER BY fecha DESC LIMIT $2
        """
        v = await fetch_all(ventas_q, nit_colegio, limit)
        r = await fetch_all(recargas_q, nit_colegio, limit)
    else:
        v = await fetch_all(
            "SELECT 'venta' AS kind, fecha AS ts, nombre_estudiante, nombre_producto, "
            "(CAST(precio AS NUMERIC) * CAST(cantidad AS INT)) AS amount FROM hackaton_ventas "
            "ORDER BY fecha DESC LIMIT $1",
            limit,
        )
        r = await fetch_all(
            "SELECT 'recarga' AS kind, fecha::text AS ts, nombre_estudiante, NULL AS nombre_producto, valor AS amount "
            "FROM hackaton_recargas ORDER BY fecha DESC LIMIT $1",
            limit,
        )
    merged = []
    for row in v + r:
        merged.append({
            "timestamp": str(row["ts"]),
            "kind": row["kind"],
            "title": row["nombre_estudiante"] or "",
            "detail": (row["nombre_producto"] or "Recarga") + f" — ${float(row['amount'] or 0):,.0f}",
        })
    merged.sort(key=lambda x: x["timestamp"], reverse=True)
    return merged[:limit]
