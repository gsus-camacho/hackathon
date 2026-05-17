"""Recommendations API routes - Personalized AI recommendations."""
import logging
from typing import Optional, Dict, List
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/recommendations", tags=["recommendations"])


class PatternAnalysisRequest(BaseModel):
    """Request for purchase pattern analysis."""
    usuario_identificacion: str = Field(..., description="Student ID")
    days: int = Field(30, ge=1, le=90, description="Analysis period in days")


class ProductRecommendationRequest(BaseModel):
    """Request for product recommendations."""
    usuario_identificacion: str = Field(..., description="Student ID")


class PackageRecommendationRequest(BaseModel):
    """Request for package recommendations."""
    identificacion_padre: str = Field(..., description="Parent ID")


class GroupComparisonRequest(BaseModel):
    """Request for group comparison."""
    usuario_identificacion: str = Field(..., description="Student ID")
    nit_colegio: Optional[str] = Field(None, description="School NIT for comparison group")


@router.get("/patterns/{usuario_identificacion}")
async def analyze_purchase_patterns(
    usuario_identificacion: str,
    days: int = 30
):
    """
    Analyze a student's purchase patterns over a period.
    Returns comprehensive pattern analysis including:
    - Top products
    - Spending habits
    - Category preferences
    - Time patterns
    """
    from backend.services.recommendation_engine import get_recommendation_engine
    
    engine = get_recommendation_engine()
    result = await engine.analyze_purchase_patterns(usuario_identificacion, days)
    
    if "error" in result:
        raise HTTPException(status_code=404, detail=result["error"])
    
    return result


@router.get("/products/{usuario_identificacion}")
async def get_product_recommendations(usuario_identificacion: str):
    """
    Get personalized product recommendations based on purchase history.
    Uses AI to suggest similar or complementary products.
    """
    from backend.services.recommendation_engine import get_recommendation_engine
    
    engine = get_recommendation_engine()
    recommendations = await engine.get_similar_product_recommendations(usuario_identificacion)
    
    return {
        "usuario_identificacion": usuario_identificacion,
        "recommendations": recommendations,
        "count": len(recommendations)
    }


@router.get("/packages/{identificacion_padre}")
async def get_package_recommendations(identificacion_padre: str):
    """
    Get personalized package recommendations for a parent.
    Analyzes spending patterns to suggest the best package.
    """
    from backend.services.recommendation_engine import get_recommendation_engine
    
    engine = get_recommendation_engine()
    recommendation = await engine.get_personalized_package_recommendation(identificacion_padre)
    
    if "error" in recommendation:
        raise HTTPException(status_code=404, detail=recommendation["error"])
    
    return recommendation


@router.get("/new-products")
async def check_new_products(nit_colegio: Optional[str] = None):
    """
    Check for new products that match student preferences.
    Returns products that appeared recently and their potential matches.
    """
    from backend.services.recommendation_engine import get_recommendation_engine
    
    engine = get_recommendation_engine()
    alerts = await engine.check_new_product_alerts(nit_colegio)
    
    return {
        "alerts": alerts,
        "count": len(alerts)
    }


@router.get("/compare/{usuario_identificacion}")
async def compare_to_group(
    usuario_identificacion: str,
    nit_colegio: Optional[str] = None
):
    """
    Compare a student's consumption to group average.
    Helps identify if a student is spending significantly more or less than peers.
    """
    from backend.services.recommendation_engine import get_recommendation_engine
    
    engine = get_recommendation_engine()
    comparison = await engine.compare_to_group_average(usuario_identificacion, nit_colegio)
    
    if "error" in comparison:
        raise HTTPException(status_code=404, detail=comparison["error"])
    
    return comparison


@router.post("/analyze/bulk")
async def bulk_analyze(request: Dict):
    """
    Analyze patterns for multiple students at once.
    Useful for school-wide reports.
    
    Request body:
    {
        "student_ids": ["id1", "id2", ...],
        "days": 30,
        "nit_colegio": "optional_school_nit"
    }
    """
    from backend.services.recommendation_engine import get_recommendation_engine
    
    engine = get_recommendation_engine()
    student_ids = request.get("student_ids", [])
    days = request.get("days", 30)
    
    if not student_ids:
        raise HTTPException(status_code=400, detail="No student IDs provided")
    
    results = []
    for uid in student_ids[:10]:  # Limit to 10 students per request
        patterns = await engine.analyze_purchase_patterns(uid, days)
        if "error" not in patterns:
            results.append(patterns)
    
    return {
        "analyzed": len(results),
        "results": results
    }


@router.get("/summary/{nit_colegio}")
async def get_school_summary(nit_colegio: str):
    """
    Get a summary of consumption patterns for an entire school.
    """
    from core.postgres import fetch_all, fetch_one
    
    try:
        # Get total students
        students_query = """
            SELECT COUNT(DISTINCT usuario_identificacion) as student_count
            FROM hackaton_ventas
            WHERE nit_colegio = $1 AND fecha >= CURRENT_DATE - INTERVAL '30 days'
        """
        students_result = await fetch_one(students_query, nit_colegio)
        student_count = students_result["student_count"] if students_result else 0
        
        # Get total revenue
        revenue_query = """
            SELECT SUM(CAST(precio AS INTEGER) * CAST(cantidad AS INTEGER)) as total
            FROM hackaton_ventas
            WHERE nit_colegio = $1 AND fecha >= CURRENT_DATE - INTERVAL '30 days'
        """
        revenue_result = await fetch_one(revenue_query, nit_colegio)
        total_revenue = float(revenue_result["total"]) if revenue_result else 0
        
        # Get top categories
        category_query = """
            SELECT 
                CASE 
                    WHEN LOWER(nombre_producto) LIKE '%jugo%' OR LOWER(nombre_producto) LIKE '%agua%' THEN 'bebida'
                    WHEN LOWER(nombre_producto) LIKE '%arepa%' OR LOWER(nombre_producto) LIKE '%perro%' THEN 'comida_rapida'
                    WHEN LOWER(nombre_producto) LIKE '%galleta%' OR LOWER(nombre_producto) LIKE '%chips%' THEN 'snack'
                    WHEN LOWER(nombre_producto) LIKE '%fruta%' OR LOWER(nombre_producto) LIKE '%ensalada%' THEN 'fruta'
                    ELSE 'general'
                END as category,
                COUNT(*) as count,
                SUM(CAST(precio AS INTEGER) * CAST(cantidad AS INTEGER)) as revenue
            FROM hackaton_ventas
            WHERE nit_colegio = $1 AND fecha >= CURRENT_DATE - INTERVAL '30 days'
            GROUP BY category
            ORDER BY count DESC
        """
        category_results = await fetch_all(category_query, nit_colegio)
        categories = [dict(r) for r in category_results]
        
        return {
            "nit_colegio": nit_colegio,
            "student_count": student_count,
            "total_revenue": round(total_revenue, 2),
            "avg_revenue_per_student": round(total_revenue / student_count, 2) if student_count > 0 else 0,
            "category_distribution": categories,
            "period_days": 30
        }
        
    except Exception as e:
        logger.error(f"Error getting school summary: {e}")
        raise HTTPException(status_code=500, detail=str(e))