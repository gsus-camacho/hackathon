"""Statistics service: composes KPIs, benchmarks, satisfaction scores."""
from typing import Optional, Dict, List
from modules.statistics import repository as repo
from modules.feedback import repository as fb_repo
from modules.planifications import repository as plan_repo
from modules.notifications import repository as notif_repo
from modules.recommendations import repository as rec_repo


async def dashboard_kpis(nit_colegio: Optional[str] = None) -> Dict:
    rev = await repo.get_school_revenue(nit_colegio, days=30)
    rec_total = await repo.get_recargas_total(nit_colegio, days=30)
    fb_summary = await fb_repo.aggregate_per_product(nit_colegio)
    total_up = sum(r["up"] for r in fb_summary)
    total_down = sum(r["down"] for r in fb_summary)
    total_votes = total_up + total_down
    avg_score = (total_up / total_votes * 100) if total_votes else 0
    students_at_risk = await plan_repo.count_students_at_risk(nit_colegio)
    bot_today = await notif_repo.count_sessions_today()
    allergens = await rec_repo.count_allergens(nit_colegio)
    return {
        "active_alerts": allergens + students_at_risk,
        "students_at_risk": students_at_risk,
        "package_revenue": float(rev.get("revenue", 0) or 0),
        "satisfaction_score": round(avg_score, 1),
        "total_students": int(rev.get("students", 0) or 0),
        "total_revenue_30d": float(rev.get("revenue", 0) or 0),
        "total_recargas_30d": rec_total,
        "bot_sessions_today": bot_today,
        "allergen_profiles": allergens,
        "feedback_votes": total_votes,
    }


async def benchmark_school(nit_colegio: str) -> List[Dict]:
    school_avg = await repo.get_school_avg_revenue_per_student(nit_colegio, 30)
    net_avg = await repo.get_network_avg_revenue_per_student(30)
    delta = ((school_avg - net_avg) / net_avg * 100) if net_avg else 0
    return [
        {
            "metric": "Ticket promedio (30d)",
            "school_value": round(school_avg, 2),
            "network_avg": round(net_avg, 2),
            "network_top": round(net_avg * 1.5, 2),
            "delta_vs_avg_pct": round(delta, 1),
        }
    ]


async def school_score(nit_colegio: str) -> float:
    """Composite health score 0-100."""
    school_avg = await repo.get_school_avg_revenue_per_student(nit_colegio, 30)
    net_avg = await repo.get_network_avg_revenue_per_student(30)
    fb_rows = await fb_repo.aggregate_per_product(nit_colegio)
    total_up = sum(r["up"] for r in fb_rows)
    total_down = sum(r["down"] for r in fb_rows)
    total_votes = total_up + total_down
    rating_pct = (total_up / total_votes * 100) if total_votes else 0
    risk = await plan_repo.count_students_at_risk(nit_colegio)
    rev_score = min(100, (school_avg / net_avg * 50)) if net_avg else 50
    rating_score = (rating_pct / 100) * 30
    risk_score = max(0, 20 - min(risk, 20))
    return round(rev_score + rating_score + risk_score, 1)


async def daily_series(nit_colegio: Optional[str] = None, days: int = 14) -> List[Dict]:
    return await repo.get_daily_series(nit_colegio, days)


async def top_products(nit_colegio: Optional[str] = None, limit: int = 8) -> List[Dict]:
    return await repo.get_top_products(nit_colegio, limit, 30)


async def recent_activity(nit_colegio: Optional[str] = None, limit: int = 12) -> List[Dict]:
    return await repo.get_recent_activity(nit_colegio, limit)


async def list_schools(limit: int = 200) -> List[Dict]:
    return await repo.get_schools(limit)
