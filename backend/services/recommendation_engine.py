"""Recommendation engine - Personalized AI-powered recommendations."""
import logging
from typing import Optional, Dict, List, Any
from datetime import datetime, timezone, timedelta
from core.postgres import fetch_all, fetch_one
from integrations.gemini_client import chat_json, chat_send
from modules.recommendations import service as rec_svc
from modules.discounts import service as disc_svc
from modules.planifications import service as plan_svc

logger = logging.getLogger(__name__)

# AI prompts for recommendation generation
PRODUCT_RECOMMENDATION_PROMPT = """Eres un nutricionista escolar experto en recomendaciones personalizadas para estudiantes.
Analiza los patrones de consumo del estudiante y recomienda 3-5 productos similares o complementarios.

Datos del estudiante:
- Productos más comprados: {top_products}
- Frecuencia de compra: {frequency}
- Presupuesto promedio diario: ${daily_avg}
- Categoría preferida: {preferred_category}

Recomienda productos que:
1. Sean similares a lo que ya compra (mismos nutrientes)
2. Ofrezcan mejor valor nutricional
3. Mantengan el presupuesto similar

Devuelve JSON: {{"recommendations": [{{"product": "nombre", "reason": "por qué lo recomiendas", "category": "categoria", "estimated_price": 5000}}]}}"""

PACKAGE_RECOMMENDATION_PROMPT = """Eres un asesor financiero escolar. Analiza los patrones de recarga y consumo para recomendar el paquete ideal.

Datos del padre:
- Recargas promedio: ${avg_recharge} cada {recharge_frequency} días
- Gasto diario promedio: ${daily_spend}
- Saldo actual: ${current_balance}
- Días restantes estimados: {days_remaining}

Recomienda el mejor paquete considerando:
1. Estabilidad financiera (evitar quedarse sin saldo)
2. Ahorro máximo
3. Flexibilidad

Devuelve JSON: {{"recommended_package": "nombre", "reason": "explicación", "savings": "ahorro estimado", "action": "llamado a la acción"}}"""

NEW_PRODUCT_ALERT_PROMPT = """Eres un asistente de novedades de cafetería escolar.
Un nuevo producto ha sido añadido al menú y coincide con los patrones del estudiante.

Producto nuevo: {new_product}
Categoría: {category}
Precio: ${price}

Patrones del estudiante:
- Productos similares que compra: {similar_products}
- Frecuencia: {frequency}

Genera un mensaje corto y atractivo (máx 3 líneas) para notificar al padre sobre este nuevo producto."""


class RecommendationEngine:
    """AI-powered personalized recommendation engine."""
    
    async def analyze_purchase_patterns(self, uid: str, days: int = 30) -> Dict[str, Any]:
        """
        Analyze student's purchase patterns over the last N days.
        Returns comprehensive pattern analysis.
        """
        try:
            # Get all purchases
            query = """
                SELECT 
                    nombre_producto,
                    CAST(precio AS INTEGER) as precio,
                    CAST(cantidad AS INTEGER) as cantidad,
                    DATE(fecha) as fecha,
                    TO_CHAR(fecha, 'HH24:MI') as hora
                FROM hackaton_ventas
                WHERE usuario_identificacion = $1 
                  AND fecha >= CURRENT_DATE - INTERVAL '{days} days'
                ORDER BY fecha DESC, fecha DESC
            """.format(days=days)
            
            purchases = await fetch_all(query, uid)
            
            if not purchases:
                return {"error": "No hay datos de consumo suficientes"}
            
            # Analyze patterns
            product_counts = {}
            category_counts = {}
            daily_totals = {}
            hourly_counts = {}
            total_spent = 0
            
            for p in purchases:
                name = p["nombre_producto"]
                price = int(p["precio"])
                qty = int(p["cantidad"])
                date = str(p["fecha"])
                hour = p.get("hora", "12:00")[:2]  # Extract hour
                
                product_counts[name] = product_counts.get(name, 0) + 1
                total_spent += price * qty
                
                daily_totals[date] = daily_totals.get(date, 0) + price * qty
                
                hour_key = f"{hour}:00"
                hourly_counts[hour_key] = hourly_counts.get(hour_key, 0) + 1
                
                # Categorize (simple heuristic)
                category = self._categorize_product(name)
                category_counts[category] = category_counts.get(category, 0) + 1
            
            # Top products
            top_products = sorted(product_counts.items(), key=lambda x: x[1], reverse=True)[:10]
            
            # Preferred category
            preferred_category = max(category_counts.items(), key=lambda x: x[1])[0] if category_counts else "general"
            
            # Average daily spend
            active_days = len(daily_totals)
            daily_avg = total_spent / active_days if active_days > 0 else 0
            
            # Purchase frequency
            frequency = active_days / days if days > 0 else 0
            
            return {
                "usuario_identificacion": uid,
                "analysis_period_days": days,
                "total_purchases": len(purchases),
                "total_spent": total_spent,
                "active_days": active_days,
                "daily_avg": round(daily_avg, 2),
                "frequency": round(frequency, 2),
                "top_products": [{"name": name, "count": count} for name, count in top_products],
                "preferred_category": preferred_category,
                "category_distribution": category_counts,
                "hourly_distribution": hourly_counts,
            }
            
        except Exception as e:
            logger.error(f"Error analyzing purchase patterns: {e}")
            return {"error": str(e)}
    
    def _categorize_product(self, product_name: str) -> str:
        """Categorize a product by name."""
        name_lower = product_name.lower()
        
        categories = {
            "bebida": ["jugo", "agua", "gaseosa", "limonada", "té", "café", "chocolatina"],
            "comida_rapida": ["arepa", "perro", "hamburguesa", "empanada", "pastel", "pan"],
            "snack": ["chips", "galleta", "chocolatina", "dulce", "paqueta"],
            "fruta": ["fruta", "ensalada", "mandarina", "manzana", "banano", "uva"],
            "lácteo": ["yogur", "leche", "queso", "kumis"],
            "comida_completa": ["almuerzo", "menú", "corriente", "ejecutivo"],
        }
        
        for category, keywords in categories.items():
            if any(keyword in name_lower for keyword in keywords):
                return category
        
        return "general"
    
    async def get_similar_product_recommendations(self, uid: str) -> List[Dict]:
        """
        Get product recommendations based on student's purchase history.
        """
        # Analyze patterns
        patterns = await self.analyze_purchase_patterns(uid, days=30)
        
        if "error" in patterns:
            return []
        
        # Format for AI prompt
        top_products_str = "\n".join([
            f"- {p['name']} ({p['count']} veces)"
            for p in patterns["top_products"][:5]
        ])
        
        prompt = PRODUCT_RECOMMENDATION_PROMPT.format(
            top_products=top_products_str,
            frequency=f"{patterns['frequency']:.1f} días/semana",
            daily_avg=f"{patterns['daily_avg']:,.0f}",
            preferred_category=patterns["preferred_category"]
        )
        
        try:
            result = await chat_json(
                session_id=f"product-rec-{uid}-{datetime.now(timezone.utc).timestamp()}",
                system_message="Eres un nutricionista escolar experto.",
                user_text=prompt
            )
            
            recommendations = result.get("recommendations", []) if isinstance(result, dict) else []
            
            # Enrich with actual product data if available
            enriched = []
            for rec in recommendations:
                if isinstance(rec, dict):
                    enriched.append({
                        "product_name": rec.get("product", "Producto"),
                        "reason": rec.get("reason", ""),
                        "category": rec.get("category", "general"),
                        "estimated_price": rec.get("estimated_price", 0),
                        "confidence": 0.8  # AI confidence
                    })
            
            return enriched[:5]
            
        except Exception as e:
            logger.error(f"Error generating product recommendations: {e}")
            return []
    
    async def get_personalized_package_recommendation(self, parent_id: str) -> Dict:
        """
        Get personalized package recommendation for a parent.
        """
        try:
            # Get parent's students
            from backend.services.parent_resolver import get_parent_students
            students = await get_parent_students(parent_id)
            
            if not students:
                return {"error": "No se encontraron estudiantes"}
            
            # Analyze spending patterns across all students
            total_spent = 0
            total_days = 0
            
            for student in students:
                uid = student["usuario_identificacion"]
                bal = await plan_svc.predict_balance(uid)
                if bal:
                    total_spent += bal.get("current_balance", 0)
                    total_days += bal.get("days_remaining", 0)
            
            avg_recharge = total_spent / len(students) if students else 0
            avg_daily_spend = total_spent / total_days if total_days > 0 else 0
            days_remaining = total_days / len(students) if students else 0
            
            # Estimate recharge frequency (rough estimate)
            recharge_frequency = max(int(total_days / 2), 1)
            
            # Get available packages
            packages = await disc_svc.list_packages()
            
            # Format for AI
            prompt = PACKAGE_RECOMMENDATION_PROMPT.format(
                avg_recharge=f"{avg_recharge:,.0f}",
                recharge_frequency=recharge_frequency,
                daily_spend=f"{avg_daily_spend:,.0f}",
                current_balance=f"{total_spent:,.0f}",
                days_remaining=int(days_remaining)
            )
            
            result = await chat_json(
                session_id=f"package-rec-{parent_id}-{datetime.now(timezone.utc).timestamp()}",
                system_message="Eres un asesor financiero escolar.",
                user_text=prompt
            )
            
            recommendation = result if isinstance(result, dict) else {}
            
            # Find matching package
            matched_package = None
            rec_name = recommendation.get("recommended_package", "").lower()
            for pkg in packages:
                if pkg["name"].lower() in rec_name or rec_name in pkg["name"].lower():
                    matched_package = pkg
                    break
            
            return {
                "recommended_package": recommendation.get("recommended_package", "Paquete Personalizado"),
                "reason": recommendation.get("reason", ""),
                "savings": recommendation.get("savings", ""),
                "action": recommendation.get("action", "Contacta al administrador para adquirir este paquete"),
                "matched_package": matched_package,
                "analysis": {
                    "avg_recharge": round(avg_recharge, 2),
                    "daily_spend": round(avg_daily_spend, 2),
                    "days_remaining": int(days_remaining),
                    "students_count": len(students)
                }
            }
            
        except Exception as e:
            logger.error(f"Error generating package recommendation: {e}")
            return {"error": str(e)}
    
    async def check_new_product_alerts(self, nit_colegio: Optional[str] = None) -> List[Dict]:
        """
        Check for new products that match student preferences.
        """
        alerts = []
        
        try:
            # Get products added in last 7 days
            query = """
                SELECT DISTINCT nombre_producto, 
                       MIN(fecha) as first_seen,
                       COUNT(*) as times_sold
                FROM hackaton_ventas
                WHERE fecha >= CURRENT_DATE - INTERVAL '7 days'
                GROUP BY nombre_producto
                HAVING COUNT(*) >= 1
                ORDER BY MIN(fecha) DESC
            """
            
            recent_products = await fetch_all(query)
            
            # Get products that are "new" (first time appearing)
            for product in recent_products[:10]:
                name = product["nombre_producto"]
                
                # Check if this product existed before last week
                old_query = """
                    SELECT COUNT(*) as cnt FROM hackaton_ventas
                    WHERE nombre_producto = $1 
                      AND fecha < CURRENT_DATE - INTERVAL '7 days'
                """
                old_result = await fetch_one(old_query, name)
                
                if old_result and int(old_result["cnt"]) > 0:
                    continue  # Not a new product
                
                # Find students who might like this
                category = self._categorize_product(name)
                
                # Get students with matching preferences
                match_query = """
                    SELECT DISTINCT v.usuario_identificacion, v.nombre_estudiante,
                           h.identificacion_padre
                    FROM hackaton_ventas v
                    LEFT JOIN hackaton_hijos h ON v.usuario_identificacion = h.usuario_identificacion
                    WHERE v.fecha >= CURRENT_DATE - INTERVAL '30 days'
                """
                # This is simplified - in production, you'd match by category preference
                matching_students = await fetch_all(match_query)
                
                if matching_students:
                    alerts.append({
                        "product": name,
                        "category": category,
                        "first_seen": str(product["first_seen"]),
                        "potential_matches": len(matching_students),
                        "status": "new_product_detected"
                    })
            
        except Exception as e:
            logger.error(f"Error checking new product alerts: {e}")
        
        return alerts
    
    async def generate_new_product_message(
        self, 
        product_name: str, 
        student_patterns: Dict
    ) -> str:
        """
        Generate a personalized message about a new product.
        """
        similar_products = "\n".join([
            f"- {p['name']}" for p in student_patterns.get("top_products", [])[:3]
        ])
        
        prompt = NEW_PRODUCT_ALERT_PROMPT.format(
            new_product=product_name,
            category=student_patterns.get("preferred_category", "general"),
            price=student_patterns.get("daily_avg", 5000),
            similar_products=similar_products or "Varios productos",
            frequency=f"{student_patterns.get('frequency', 3)} veces/semana"
        )
        
        try:
            message = await chat_send(
                session_id=f"new-product-msg-{datetime.now(timezone.utc).timestamp()}",
                system_message="Eres un asistente de novedades de cafetería escolar.",
                user_text=prompt
            )
            return message
        except Exception as e:
            logger.error(f"Error generating new product message: {e}")
            return f"🆕 Nuevo producto: {product_name}. ¡Pruébalo!"
    
    async def compare_to_group_average(
        self, 
        uid: str, 
        nit_colegio: Optional[str] = None
    ) -> Dict:
        """
        Compare student's consumption to group average.
        """
        # Get student's patterns
        student_patterns = await self.analyze_purchase_patterns(uid, days=30)
        
        if "error" in student_patterns:
            return {"error": "No hay datos suficientes"}
        
        # Get group average
        if nit_colegio:
            avg_query = """
                SELECT 
                    AVG(daily_total) as avg_daily,
                    COUNT(DISTINCT usuario_identificacion) as student_count
                FROM (
                    SELECT 
                        usuario_identificacion,
                        DATE(fecha) as date,
                        SUM(CAST(precio AS INTEGER) * CAST(cantidad AS INTEGER)) as daily_total
                    FROM hackaton_ventas
                    WHERE nit_colegio = $1 
                      AND fecha >= CURRENT_DATE - INTERVAL '30 days'
                    GROUP BY usuario_identificacion, DATE(fecha)
                ) daily_spends
                GROUP BY usuario_identificacion
            """
            group_result = await fetch_one(avg_query, nit_colegio)
        else:
            avg_query = """
                SELECT 
                    AVG(daily_total) as avg_daily,
                    COUNT(DISTINCT usuario_identificacion) as student_count
                FROM (
                    SELECT 
                        usuario_identificacion,
                        DATE(fecha) as date,
                        SUM(CAST(precio AS INTEGER) * CAST(cantidad AS INTEGER)) as daily_total
                    FROM hackaton_ventas
                    WHERE fecha >= CURRENT_DATE - INTERVAL '30 days'
                    GROUP BY usuario_identificacion, DATE(fecha)
                ) daily_spends
                GROUP BY usuario_identificacion
            """
            group_result = await fetch_one(avg_query)
        
        group_avg = float(group_result["avg_daily"]) if group_result else 0
        student_count = int(group_result["student_count"]) if group_result else 0
        
        student_daily = student_patterns.get("daily_avg", 0)
        
        # Calculate difference
        if group_avg > 0:
            diff_pct = ((student_daily - group_avg) / group_avg) * 100
        else:
            diff_pct = 0
        
        return {
            "student_daily_avg": round(student_daily, 2),
            "group_daily_avg": round(group_avg, 2),
            "difference_pct": round(diff_pct, 2),
            "student_count": student_count,
            "status": "above_average" if diff_pct > 20 else ("below_average" if diff_pct < -20 else "average"),
            "message": self._generate_comparison_message(diff_pct, student_daily, group_avg)
        }
    
    def _generate_comparison_message(
        self, 
        diff_pct: float, 
        student_avg: float, 
        group_avg: float
    ) -> str:
        """Generate a message comparing student to group."""
        if diff_pct > 40:
            return (
                f"⚠️ El consumo de este estudiante es {diff_pct:.0f}% mayor al promedio.\n"
                f"Estudiante: ${student_avg:,.0f}/día | Promedio: ${group_avg:,.0f}/día"
            )
        elif diff_pct > 20:
            return (
                f"📈 El consumo es ligeramente superior ({diff_pct:.0f}%) al promedio.\n"
                f"Estudiante: ${student_avg:,.0f}/día | Promedio: ${group_avg:,.0f}/día"
            )
        elif diff_pct < -40:
            return (
                f"⚠️ El consumo es {abs(diff_pct):.0f}% menor al promedio.\n"
                f"Estudiante: ${student_avg:,.0f}/día | Promedio: ${group_avg:,.0f}/día"
            )
        elif diff_pct < -20:
            return (
                f"📉 El consumo es ligeramente inferior ({abs(diff_pct):.0f}%) al promedio.\n"
                f"Estudiante: ${student_avg:,.0f}/día | Promedio: ${group_avg:,.0f}/día"
            )
        else:
            return (
                f"✅ El consumo está dentro del rango promedio.\n"
                f"Estudiante: ${student_avg:,.0f}/día | Promedio: ${group_avg:,.0f}/día"
            )


# Singleton instance
_recommendation_engine: Optional[RecommendationEngine] = None


def get_recommendation_engine() -> RecommendationEngine:
    """Get the singleton RecommendationEngine instance."""
    global _recommendation_engine
    if _recommendation_engine is None:
        _recommendation_engine = RecommendationEngine()
    return _recommendation_engine