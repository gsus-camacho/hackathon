"""Recommendations service: AI-powered insights via Gemini."""
from typing import Optional, List, Dict
import uuid
from datetime import datetime, timezone
from integrations.gemini_client import chat_json
from modules.recommendations import repository as repo
from modules.recommendations.schemas import Allergen, AllergenCreate, RecommendationRequest
from modules.recommendations.errors import AIBackendError
from modules.statistics import repository as stats_repo


SYSTEM_PROMPT = """Eres un nutricionista escolar y analista de datos para BioAlert+, un sistema que monitorea ventas de cafeterías escolares en Colombia.
Tu trabajo es proponer recomendaciones accionables basadas en datos de consumo para directores y nutricionistas.
Devuelve UN array JSON con 3-4 recomendaciones, cada una con esta estructura exacta:
{"title": "string corto", "summary": "1-2 frases", "rationale": "2-3 frases con racional basado en los datos", "kind": "product|package|nutrition|operational", "impact_score": 0-100}
Sé directo, usa español neutro, evita generalidades, basa todo en los datos enviados."""


async def personalized_recommendations(usuario_identificacion: str, nit_colegio: Optional[str] = None, days: int = 30) -> List[Dict]:
    top_products = await stats_repo.get_student_top_products(usuario_identificacion, limit=5, days=days)
    avg_spend = await stats_repo.get_student_avg_spend(usuario_identificacion, days=days)
    school_avg = await stats_repo.get_school_avg_revenue_per_student(nit_colegio, days) if nit_colegio else 0.0
    products = [p["name"] for p in top_products]
    recs = [
        {
            "title": "Paquete semanal personalizado",
            "summary": (
                f"Basado en el consumo promedio de ${avg_spend:,.0f}/día, sugerimos un paquete semanal de 5 días "
                f"con un 5% de descuento para estabilidad de saldo."
            ),
            "rationale": (
                "Tu hijo compra frecuentemente " + ", ".join(products[:3]) + ". "
                f"Promover un paquete fijo reduce recargas frecuentes y estabiliza el presupuesto."
            ),
            "kind": "package",
            "impact_score": min(95, max(30, int(avg_spend / 500))),
            "data": {
                "usuario_identificacion": usuario_identificacion,
                "avg_daily_spend": avg_spend,
                "top_products": products,
            },
        }
    ]
    if school_avg and school_avg > 0:
        recs.append({
            "title": "Ajuste de consumo frente al promedio escolar",
            "summary": (
                f"Tu hijo gasta en promedio ${avg_spend:,.0f}/día, frente a ${school_avg:,.0f}/día del colegio."
            ),
            "rationale": (
                "Es útil equilibrar la alimentación con opciones similares pero más económicas cuando el gasto personal supera la media escolar."
            ),
            "kind": "nutrition",
            "impact_score": min(90, max(20, int(100 - abs(avg_spend - school_avg) / max(school_avg, 1) * 100))),
            "data": {
                "avg_daily_spend": avg_spend,
                "school_avg_daily": school_avg,
            },
        })
    return recs


async def package_offer(usuario_identificacion: str, nit_colegio: Optional[str] = None) -> Dict[str, Dict[str, object]]:
    avg_spend = await stats_repo.get_student_avg_spend(usuario_identificacion, days=30)
    if avg_spend <= 0:
        avg_spend = 12000.0
    weekly_price = round(avg_spend * 5 * 0.95, 2)
    monthly_price = round(avg_spend * 20 * 0.9, 2)
    return {
        "weekly": {
            "name": "Paquete Semanal",
            "days": 5,
            "estimated_daily": round(avg_spend, 2),
            "discount_pct": 5,
            "price": weekly_price,
            "savings": round(avg_spend * 5 - weekly_price, 2),
        },
        "monthly": {
            "name": "Paquete Mensual",
            "days": 20,
            "estimated_daily": round(avg_spend, 2),
            "discount_pct": 10,
            "price": monthly_price,
            "savings": round(avg_spend * 20 - monthly_price, 2),
        },
    }


async def analyze_student_consumption(usuario_identificacion: str, days: int = 7) -> Dict[str, object]:
    purchases = await stats_repo.get_student_recent_purchases(usuario_identificacion, days=days, limit=20)
    total = sum(p["total"] for p in purchases)
    return {
        "usuario_identificacion": usuario_identificacion,
        "days": days,
        "total_spent": round(total, 2),
        "purchase_count": len(purchases),
        "products": [p["product"] for p in purchases[:5]],
    }


async def generate_recommendations(req: RecommendationRequest) -> List[Dict]:
    top = await stats_repo.get_top_products(req.nit_colegio, 8, 30)
    rev = await stats_repo.get_school_revenue(req.nit_colegio, 30)
    user_text = (
        f"Foco: {req.focus}\n"
        f"Colegio NIT: {req.nit_colegio or 'red completa'}\n"
        f"Ingresos 30d: ${float(rev.get('revenue', 0)):,.0f}\n"
        f"Estudiantes activos: {int(rev.get('students', 0))}\n"
        f"Top productos:\n"
    )
    for p in top:
        user_text += f"- {p['name']}: {p['units']} u, ${p['revenue']:,.0f}\n"
    user_text += '\nGenera el JSON ahora. La salida debe ser SOLO {"recommendations": [...]}'

    try:
        result = await chat_json(
            session_id=f"rec-{req.nit_colegio or 'global'}-{datetime.now(timezone.utc).timestamp()}",
            system_message=SYSTEM_PROMPT,
            user_text=user_text,
        )
    except Exception as e:
        raise AIBackendError(str(e))

    recs = result.get("recommendations") if isinstance(result, dict) else None
    if not recs and isinstance(result, list):
        recs = result
    if not recs:
        recs = _build_sample_recommendations(top, req.focus)

    saved = []
    for r in recs:
        if not isinstance(r, dict):
            continue
        doc = {
            "id": str(uuid.uuid4()),
            "nit_colegio": req.nit_colegio,
            "usuario_identificacion": None,
            "kind": r.get("kind", "operational"),
            "title": r.get("title", "Recomendación"),
            "summary": r.get("summary", ""),
            "rationale": r.get("rationale", ""),
            "impact_score": float(r.get("impact_score", 50)),
            "data": {"focus": req.focus},
            "created_at": datetime.now(timezone.utc).isoformat(),
        }
        await repo.insert_recommendation(doc)
        saved.append(doc)
    return saved


def _build_sample_recommendations(top_products: List[Dict], focus: str) -> List[Dict]:
    if not top_products:
        top_products = [
            {"name": "Arepa de huevo", "units": 45, "revenue": 540000},
            {"name": "Jugo natural", "units": 38, "revenue": 304000},
            {"name": "Wrap de pollo", "units": 29, "revenue": 261000},
        ]

    highlights = ", ".join([p["name"] for p in top_products[:3]])
    recommendations = [
        {
            "title": "Ajusta el surtido a los productos más vendidos",
            "summary": f"Los datos recientes muestran que {highlights} concentran la mayor parte del ticket medio.",
            "rationale": "Potenciar estos productos reduce desperdicio y aumenta el ingreso promedio por estudiante.",
            "kind": "product",
            "impact_score": 82,
        },
        {
            "title": "Lanza un paquete semanal inteligente",
            "summary": "Un paquete semanal con descuento fija el gasto y mejora la previsibilidad de recargas.",
            "rationale": "Los padres prefieren pagos únicos cuando el presupuesto es limitado y el consumo es recurrente.",
            "kind": "package",
            "impact_score": 75,
        },
    ]
    if focus == "nutrition":
        recommendations.append({
            "title": "Incluye opciones más saludables en el menú",
            "summary": "Suma frutas y bebidas naturales para equilibrar los snacks rápidos más vendidos.",
            "rationale": "Esto mejora la percepción de salud sin cambiar los hábitos de compra de los estudiantes.",
            "kind": "nutrition",
            "impact_score": 70,
        })
    elif focus == "safety":
        recommendations.append({
            "title": "Activa alertas automáticas de alérgenos",
            "summary": "Si un nuevo producto contiene maní o gluten, informa al padre de inmediato.",
            "rationale": "Reducir riesgos alimentarios protege a los estudiantes y fortalece la confianza en el servicio.",
            "kind": "safety",
            "impact_score": 88,
        })
    else:
        recommendations.append({
            "title": "Optimiza el ticket promedio con ofertas cruzadas",
            "summary": "Combina productos complementarios en promociones para aumentar ventas por compra.",
            "rationale": "Una buena oferta en el punto de venta incrementa el gasto promedio sin afectar la experiencia del padre.",
            "kind": "operational",
            "impact_score": 68,
        })
    return recommendations


async def list_recommendations(nit_colegio: Optional[str] = None) -> List[Dict]:
    return await repo.list_recommendations(nit_colegio, 30)


async def create_allergen(req: AllergenCreate) -> Dict:
    a = Allergen(**req.model_dump())
    doc = a.model_dump()
    await repo.insert_allergen(doc)
    return doc


async def list_allergens(nit_colegio: Optional[str] = None) -> List[Dict]:
    return await repo.list_allergens(nit_colegio)


async def check_allergen_risk(usuario_identificacion: str, product_name: str) -> List[str]:
    """Returns the list of matched allergens for a given product purchase."""
    allergens = await repo.get_allergens_for_student(usuario_identificacion)
    product_lower = product_name.lower()
    matched = []
    # Simple keyword matching expanded with synonyms
    keyword_map = {
        "mani": ["mani", "maní", "peanut"],
        "lactosa": ["lactosa", "leche", "queso", "yogurt", "milk"],
        "gluten": ["gluten", "trigo", "pan", "harina", "wheat"],
        "huevo": ["huevo", "egg"],
        "soya": ["soya", "soja", "soy"],
        "frutos secos": ["nuez", "almendra", "marañon", "nut"],
        "mariscos": ["camaron", "pescado", "atun", "fish"],
    }
    for a in allergens:
        keys = keyword_map.get(a.lower(), [a.lower()])
        for k in keys:
            if k in product_lower:
                matched.append(a)
                break
    return matched
