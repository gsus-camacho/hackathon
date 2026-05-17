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
        return []

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
