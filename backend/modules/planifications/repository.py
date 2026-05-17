"""Planifications repository: per-student balance calculation from Biofood data."""
from typing import Optional, List, Dict
from core.postgres import fetch_all, fetch_one


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


async def list_students_at_risk(nit_colegio: Optional[str] = None, limit: int = 50) -> List[Dict]:
    """Identify students whose remaining balance is low (< 30 days avg spend)."""
    if nit_colegio:
        q = """
            WITH ventas_agg AS (
              SELECT usuario_identificacion,
                     MAX(nombre_estudiante) AS nombre_estudiante,
                     MAX(nit_colegio) AS nit_colegio,
                     SUM(CAST(precio AS NUMERIC) * CAST(cantidad AS INT)) AS total_consumo,
                     COUNT(DISTINCT fecha) AS active_days,
                     MAX(fecha::date) AS last_consumption
              FROM hackaton_ventas WHERE nit_colegio=$1
              GROUP BY usuario_identificacion
            ),
            recargas_agg AS (
              SELECT usuario_identificacion, SUM(valor) AS total_recargas, MAX(fecha) AS last_recharge
              FROM hackaton_recargas WHERE nit_colegio=$1 GROUP BY usuario_identificacion
            )
            SELECT v.usuario_identificacion, v.nombre_estudiante, v.nit_colegio,
                   COALESCE(r.total_recargas, 0) AS total_recargas,
                   v.total_consumo,
                   COALESCE(r.total_recargas, 0) - v.total_consumo AS current_balance,
                   v.active_days,
                   v.last_consumption,
                   r.last_recharge
            FROM ventas_agg v
            LEFT JOIN recargas_agg r ON r.usuario_identificacion = v.usuario_identificacion
            WHERE COALESCE(r.total_recargas, 0) - v.total_consumo < (v.total_consumo / NULLIF(v.active_days, 0)) * 7
              AND v.active_days > 3
            ORDER BY (COALESCE(r.total_recargas, 0) - v.total_consumo) ASC
            LIMIT $2
        """
        rows = await fetch_all(q, nit_colegio, limit)
    else:
        q = """
            WITH ventas_agg AS (
              SELECT usuario_identificacion,
                     MAX(nombre_estudiante) AS nombre_estudiante,
                     MAX(nit_colegio) AS nit_colegio,
                     SUM(CAST(precio AS NUMERIC) * CAST(cantidad AS INT)) AS total_consumo,
                     COUNT(DISTINCT fecha) AS active_days,
                     MAX(fecha::date) AS last_consumption
              FROM hackaton_ventas
              GROUP BY usuario_identificacion
            ),
            recargas_agg AS (
              SELECT usuario_identificacion, SUM(valor) AS total_recargas, MAX(fecha) AS last_recharge
              FROM hackaton_recargas GROUP BY usuario_identificacion
            )
            SELECT v.usuario_identificacion, v.nombre_estudiante, v.nit_colegio,
                   COALESCE(r.total_recargas, 0) AS total_recargas,
                   v.total_consumo,
                   COALESCE(r.total_recargas, 0) - v.total_consumo AS current_balance,
                   v.active_days,
                   v.last_consumption,
                   r.last_recharge
            FROM ventas_agg v
            LEFT JOIN recargas_agg r ON r.usuario_identificacion = v.usuario_identificacion
            WHERE COALESCE(r.total_recargas, 0) - v.total_consumo < (v.total_consumo / NULLIF(v.active_days, 0)) * 7
              AND v.active_days > 3
            ORDER BY (COALESCE(r.total_recargas, 0) - v.total_consumo) ASC
            LIMIT $1
        """
        rows = await fetch_all(q, limit)
    return rows


async def count_students_at_risk(nit_colegio: Optional[str] = None) -> int:
    """Fast approximation: students who consumed in last 14 days but haven't recharged in 30+ days."""
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


async def list_students_at_risk_fast(nit_colegio: Optional[str] = None, limit: int = 50) -> List[Dict]:
    """Lighter version using sample of recent activity instead of full aggregation."""
    if nit_colegio:
        q = """
            WITH recent AS (
              SELECT DISTINCT ON (usuario_identificacion)
                     usuario_identificacion, nombre_estudiante, nit_colegio, fecha::date AS last_consumption
              FROM hackaton_ventas
              WHERE nit_colegio=$1 AND fecha::date >= CURRENT_DATE - 30
              ORDER BY usuario_identificacion, fecha DESC
            )
            SELECT r.*,
                   COALESCE((SELECT SUM(valor) FROM hackaton_recargas WHERE usuario_identificacion=r.usuario_identificacion), 0) AS total_recargas,
                   COALESCE((SELECT SUM(CAST(precio AS NUMERIC) * CAST(cantidad AS INT)) FROM hackaton_ventas WHERE usuario_identificacion=r.usuario_identificacion), 0) AS total_consumo,
                   (SELECT MAX(fecha) FROM hackaton_recargas WHERE usuario_identificacion=r.usuario_identificacion) AS last_recharge
            FROM recent r
            WHERE NOT EXISTS (
              SELECT 1 FROM hackaton_recargas rr
              WHERE rr.usuario_identificacion = r.usuario_identificacion
                AND rr.fecha >= CURRENT_DATE - 30
            )
            LIMIT $2
        """
        return await fetch_all(q, nit_colegio, limit)
    q = """
        WITH recent AS (
          SELECT DISTINCT ON (usuario_identificacion)
                 usuario_identificacion, nombre_estudiante, nit_colegio, fecha::date AS last_consumption
          FROM hackaton_ventas
          WHERE fecha::date >= CURRENT_DATE - 30
          ORDER BY usuario_identificacion, fecha DESC
        )
        SELECT r.*,
               COALESCE((SELECT SUM(valor) FROM hackaton_recargas WHERE usuario_identificacion=r.usuario_identificacion), 0) AS total_recargas,
               COALESCE((SELECT SUM(CAST(precio AS NUMERIC) * CAST(cantidad AS INT)) FROM hackaton_ventas WHERE usuario_identificacion=r.usuario_identificacion), 0) AS total_consumo,
               (SELECT MAX(fecha) FROM hackaton_recargas WHERE usuario_identificacion=r.usuario_identificacion) AS last_recharge
        FROM recent r
        WHERE NOT EXISTS (
          SELECT 1 FROM hackaton_recargas rr
          WHERE rr.usuario_identificacion = r.usuario_identificacion
            AND rr.fecha >= CURRENT_DATE - 30
        )
        LIMIT $1
    """
    return await fetch_all(q, limit)


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
