"""B2B Intelligence service: composes data for the benchmark page."""
from typing import Dict, List
from modules.statistics import b2b_repository as repo


async def full_b2b_report(days: int = 90) -> Dict:
    """
    Aggregated B2B report for the frontend benchmark page.
    Returns product benchmark, satisfaction index, network summary, and school ranking.
    """
    benchmark, summary, satisfaction, schools = await _gather(days)

    # Compute network-wide average SI
    si_values = [s["si"] for s in satisfaction if s["total_votes"] > 0]
    avg_si = round(sum(si_values) / len(si_values), 2) if si_values else 0.0

    return {
        "benchmark": benchmark,
        "satisfaction": satisfaction,
        "summary": {
            **summary,
            "avg_si": avg_si,
            "days": days,
        },
        "schools": schools,
    }


async def _gather(days: int):
    import asyncio
    return await asyncio.gather(
        repo.get_product_benchmark(days=days, limit=12),
        repo.get_network_summary(days=days),
        repo.get_product_satisfaction(),
        repo.get_schools_ranking(days=days, limit=30),
    )
