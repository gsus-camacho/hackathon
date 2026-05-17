"""B2B Intelligence repository: heavy aggregations for benchmark page."""
from typing import Optional, List, Dict
from core.postgres import fetch_all, fetch_one


async def get_product_benchmark(days: int = 90, limit: int = 12) -> List[Dict]:
    """
    For each top product, compute:
      - total units & revenue across the entire network
      - number of schools selling it
      - average units-per-school
    Then compute the network median (approximated as overall avg) so
    the frontend can show a delta % per product.
    """
    q = """
        WITH product_stats AS (
            SELECT
                nombre_producto,
                SUM(CAST(cantidad AS INT)) AS total_units,
                SUM(CAST(precio AS NUMERIC) * CAST(cantidad AS INT)) AS total_revenue,
                COUNT(DISTINCT nit_colegio) AS schools_selling,
                AVG(CAST(precio AS NUMERIC)) AS avg_unit_price
            FROM hackaton_ventas
            WHERE fecha::date >= CURRENT_DATE - $1::int
            GROUP BY nombre_producto
            ORDER BY total_revenue DESC
            LIMIT $2
        ),
        network_median AS (
            SELECT AVG(total_units) AS median_units
            FROM (
                SELECT nombre_producto, SUM(CAST(cantidad AS INT)) AS total_units
                FROM hackaton_ventas
                WHERE fecha::date >= CURRENT_DATE - $1::int
                GROUP BY nombre_producto
            ) sub
        )
        SELECT
            ps.nombre_producto,
            ps.total_units,
            ps.total_revenue,
            ps.schools_selling,
            ps.avg_unit_price,
            nm.median_units,
            CASE WHEN nm.median_units > 0
                THEN ROUND(((ps.total_units - nm.median_units) / nm.median_units * 100)::numeric, 1)
                ELSE 0
            END AS delta_vs_median
        FROM product_stats ps, network_median nm
        ORDER BY ps.total_revenue DESC
    """
    rows = await fetch_all(q, days, limit)
    return [
        {
            "product": r["nombre_producto"],
            "total_units": int(r["total_units"] or 0),
            "total_revenue": float(r["total_revenue"] or 0),
            "schools_selling": int(r["schools_selling"] or 0),
            "avg_unit_price": float(r["avg_unit_price"] or 0),
            "delta": float(r["delta_vs_median"] or 0),
        }
        for r in rows
    ]


async def get_network_summary(days: int = 90) -> Dict:
    """Overall network KPIs for B2B section."""
    q = """
        SELECT
            COUNT(DISTINCT nit_colegio) AS total_schools,
            COUNT(*) AS total_records,
            COUNT(DISTINCT usuario_identificacion) AS total_students,
            COUNT(DISTINCT nombre_producto) AS total_products,
            SUM(CAST(precio AS NUMERIC) * CAST(cantidad AS INT)) AS total_revenue
        FROM hackaton_ventas
        WHERE fecha::date >= CURRENT_DATE - $1::int
    """
    row = await fetch_one(q, days)
    return {
        "total_schools": int(row["total_schools"] or 0) if row else 0,
        "total_records": int(row["total_records"] or 0) if row else 0,
        "total_students": int(row["total_students"] or 0) if row else 0,
        "total_products": int(row["total_products"] or 0) if row else 0,
        "total_revenue": float(row["total_revenue"] or 0) if row else 0,
    }


async def get_product_satisfaction() -> List[Dict]:
    """
    Combine product feedback votes with sales data to build a
    Satisfaction Index per product.
    SI = (up_votes / total_votes) normalized 0-1.
    """
    from modules.feedback import repository as fb_repo

    fb_rows = await fb_repo.aggregate_per_product()
    results = []
    for r in fb_rows:
        up = int(r.get("up", 0))
        down = int(r.get("down", 0))
        total = up + down
        si = round(up / total, 2) if total > 0 else 0.0
        if si >= 0.75:
            action = "Mantener"
        elif si >= 0.50:
            action = "Revisar"
        else:
            action = "Descontinuar"
        results.append({
            "product": r.get("product_name", ""),
            "si": si,
            "action": action,
            "up": up,
            "down": down,
            "total_votes": total,
        })
    # Sort by SI descending
    results.sort(key=lambda x: x["si"], reverse=True)
    return results


async def get_schools_ranking(days: int = 90, limit: int = 30) -> List[Dict]:
    """Ranking of schools by revenue and student count."""
    q = """
        SELECT
            nit_colegio,
            colegio,
            COUNT(DISTINCT usuario_identificacion) AS total_students,
            SUM(CAST(precio AS NUMERIC) * CAST(cantidad AS INT)) AS total_revenue,
            COUNT(*) AS total_transactions,
            SUM(CAST(precio AS NUMERIC) * CAST(cantidad AS INT)) /
                NULLIF(COUNT(DISTINCT usuario_identificacion), 0) AS revenue_per_student
        FROM hackaton_ventas
        WHERE fecha::date >= CURRENT_DATE - $1::int
        GROUP BY nit_colegio, colegio
        ORDER BY total_revenue DESC
        LIMIT $2
    """
    rows = await fetch_all(q, days, limit)
    return [
        {
            "nit_colegio": r["nit_colegio"],
            "colegio": r["colegio"],
            "total_students": int(r["total_students"] or 0),
            "total_revenue": float(r["total_revenue"] or 0),
            "total_transactions": int(r["total_transactions"] or 0),
            "revenue_per_student": float(r["revenue_per_student"] or 0),
        }
        for r in rows
    ]
