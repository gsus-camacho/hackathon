"""Discounts service: builds dynamic packages from real consumption data."""
from typing import Optional, List, Dict
import uuid
from datetime import datetime, timezone, timedelta
from modules.discounts import repository as repo
from modules.discounts.schemas import Package, PackageItem, PackageCreate
from modules.discounts.errors import InvalidPackageError


async def build_dynamic_packages(nit_colegio: Optional[str] = None) -> List[Dict]:
    """Generate AI-curated bundles from top-selling products."""
    combos = await repo.get_top_combos(nit_colegio, limit=6)
    if not combos:
        return []
    packages = []

    # Bundle 1: Top 3 products
    top3 = combos[:3]
    if top3:
        original = sum(c["avg_price"] * 1 for c in top3)
        discount_pct = 10.0
        discounted = original * (1 - discount_pct / 100)
        packages.append({
            "id": str(uuid.uuid4()),
            "name": "Combo Estrella",
            "description": "Los 3 productos más vendidos con 10% de descuento.",
            "items": [{"product_name": c["name"], "quantity": 1, "unit_price": float(c["avg_price"])} for c in top3],
            "original_total": round(original, 2),
            "discounted_total": round(discounted, 2),
            "discount_pct": discount_pct,
            "target_segment": "general",
            "nit_colegio": nit_colegio,
            "valid_until": (datetime.now(timezone.utc) + timedelta(days=14)).date().isoformat(),
            "created_at": datetime.now(timezone.utc).isoformat(),
            "active": True,
        })

    # Bundle 2: Low balance offer - smaller, cheaper bundle
    if len(combos) >= 2:
        cheap = sorted(combos, key=lambda c: c["avg_price"])[:2]
        original = sum(c["avg_price"] for c in cheap)
        discount_pct = 15.0
        discounted = original * (1 - discount_pct / 100)
        packages.append({
            "id": str(uuid.uuid4()),
            "name": "Rescate Saldo Bajo",
            "description": "Pack económico ideal para estudiantes con saldo bajo. 15% off.",
            "items": [{"product_name": c["name"], "quantity": 1, "unit_price": float(c["avg_price"])} for c in cheap],
            "original_total": round(original, 2),
            "discounted_total": round(discounted, 2),
            "discount_pct": discount_pct,
            "target_segment": "low_balance",
            "nit_colegio": nit_colegio,
            "valid_until": (datetime.now(timezone.utc) + timedelta(days=7)).date().isoformat(),
            "created_at": datetime.now(timezone.utc).isoformat(),
            "active": True,
        })

    # Bundle 3: Heavy consumer - 5 items 20% off
    if len(combos) >= 5:
        items = combos[:5]
        original = sum(c["avg_price"] for c in items)
        discount_pct = 20.0
        discounted = original * (1 - discount_pct / 100)
        packages.append({
            "id": str(uuid.uuid4()),
            "name": "Mega Pack Premium",
            "description": "Para alto consumo. 5 productos top con 20% descuento.",
            "items": [{"product_name": c["name"], "quantity": 1, "unit_price": float(c["avg_price"])} for c in items],
            "original_total": round(original, 2),
            "discounted_total": round(discounted, 2),
            "discount_pct": discount_pct,
            "target_segment": "high_consumption",
            "nit_colegio": nit_colegio,
            "valid_until": (datetime.now(timezone.utc) + timedelta(days=30)).date().isoformat(),
            "created_at": datetime.now(timezone.utc).isoformat(),
            "active": True,
        })

    return packages


async def save_packages(packages: List[Dict]) -> List[Dict]:
    for p in packages:
        await repo.insert_package(p)
    return packages


async def generate_and_save(nit_colegio: Optional[str] = None) -> List[Dict]:
    pkgs = await build_dynamic_packages(nit_colegio)
    return await save_packages(pkgs)


async def list_packages(nit_colegio: Optional[str] = None) -> List[Dict]:
    return await repo.list_packages(nit_colegio)


async def create_package(req: PackageCreate) -> Dict:
    if not req.items:
        raise InvalidPackageError("Package must have at least one item")
    original = sum(i.quantity * i.unit_price for i in req.items)
    discounted = original * (1 - req.discount_pct / 100)
    p = Package(
        name=req.name,
        description=req.description,
        items=req.items,
        original_total=round(original, 2),
        discounted_total=round(discounted, 2),
        discount_pct=req.discount_pct,
        target_segment=req.target_segment,
        nit_colegio=req.nit_colegio,
        valid_until=req.valid_until,
    )
    doc = p.model_dump()
    await repo.insert_package(doc)
    return doc


async def deactivate(package_id: str) -> bool:
    return await repo.deactivate_package(package_id)


async def suggested_recharge(nit_colegio: Optional[str] = None) -> float:
    avg = await repo.avg_recharge_amount(nit_colegio)
    return round(avg, 2) if avg else 30000.0
