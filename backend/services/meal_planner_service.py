"""Meal planner service - Weekly meal planning with budget tracking and rewards."""
import logging
from typing import Optional, Dict, List, Any
from datetime import datetime, timezone, timedelta
from core.postgres import fetch_all, fetch_one
from integrations.gemini_client import chat_json, chat_send
from modules.planifications import service as plan_svc
from modules.planifications import repository as plan_repo
from modules.planifications.schemas import MealPlanCreate
from modules.discounts import service as disc_svc
from backend.services.parent_resolver import get_parent_students
from backend.services.recommendation_engine import get_recommendation_engine

logger = logging.getLogger(__name__)

# AI prompt for meal plan generation
MEAL_PLAN_PROMPT = """Eres un nutricionista escolar experto en planificación de comidas.
Genera un plan de alimentación semanal (lunes a viernes) para un estudiante.

Restricciones y preferencias:
- Presupuesto semanal: ${budget}
- Alérgenos a evitar: {allergens}
- Preferencias: {preferences}
- Categoría preferida: {preferred_category}
- Gasto diario promedio histórico: ${daily_avg}

Productos disponibles (top vendidos):
{available_products}

Genera un plan que:
1. Respete el presupuesto semanal
2. Evite alergenos
3. Ofrezca variedad nutricional
4. Se acerque a las preferencias del estudiante

Devuelve JSON: {{"plan": [{{"day": "lunes|martes|miercoles|jueves|viernes", "items": [{{"name": "producto", "price": 5000, "category": "categoria"}}], "daily_total": 10000, "notes": "nota opcional"}}], "weekly_total": 50000, "budget_met": true, "suggestions": "sugerencias adicionales"}}"""

TRACKING_FEEDBACK_PROMPT = """Analiza el cumplimiento del plan de alimentación semanal.

Plan original:
- Presupuesto: ${budget}
- Días planificados: {planned_days}

Consumo real:
{actual_consumption}

Evalúa:
1. Porcentaje de cumplimiento del presupuesto
2. Variedad nutricional mantenida
3. Recomendaciones para la próxima semana

Devuelve JSON: {{"compliance_pct": 85, "budget_status": "within_budget|over_budget|under_budget", "nutrition_score": 7, "reward_earned": true, "feedback": "mensaje para el padre", "suggestions": "sugerencias para mejorar"}}"""


class MealPlannerService:
    """Weekly meal planning with budget tracking and rewards."""
    
    # Day names for the week
    WEEKDAYS = ["lunes", "martes", "miercoles", "jueves", "viernes"]
    
    # Reward thresholds
    REWARD_COMPLIANCE_THRESHOLD = 0.9  # 90% compliance = 10% discount
    REWARD_DISCOUNT_PCT = 10
    
    async def create_weekly_plan(
        self,
        parent_id: str,
        budget: float,
        allergens: Optional[List[str]] = None,
        preferences: Optional[List[str]] = None,
        start_date: Optional[str] = None
    ) -> Dict:
        """
        Create a weekly meal plan for a parent's student.
        """
        try:
            # Get students for this parent
            students = await get_parent_students(parent_id)
            if not students:
                return {"error": "No se encontraron estudiantes"}
            
            student = students[0]  # Use first student for now
            uid = student["usuario_identificacion"]
            student_name = student.get("nombre_estudiante", uid)
            
            # Analyze student patterns
            rec_engine = get_recommendation_engine()
            patterns = await rec_engine.analyze_purchase_patterns(uid, days=30)
            
            # Get available products (top sellers)
            available_products = await self._get_available_products(
                nit_colegio=student.get("nit_colegio")
            )
            
            # Format for AI
            allergens_str = ", ".join(allergens) if allergens else "Ninguno"
            preferences_str = ", ".join(preferences) if preferences else "Ninguna"
            daily_avg = patterns.get("daily_avg", 5000)
            preferred_category = patterns.get("preferred_category", "general")
            
            products_list = "\n".join([
                f"- {p['name']} (${p.get('avg_price', 5000):,})"
                for p in available_products[:15]
            ])
            
            prompt = MEAL_PLAN_PROMPT.format(
                budget=f"{budget:,.0f}",
                allergens=allergens_str,
                preferences=preferences_str,
                daily_avg=f"{daily_avg:,.0f}",
                preferred_category=preferred_category,
                available_products=products_list
            )
            
            result = await chat_json(
                session_id=f"meal-plan-{uid}-{datetime.now(timezone.utc).timestamp()}",
                system_message="Eres un nutricionista escolar experto.",
                user_text=prompt
            )
            
            if not isinstance(result, dict) or "plan" not in result:
                return {"error": "No se pudo generar el plan"}
            
            plan_data = result
            week_start = start_date or self._get_next_monday().isoformat()
            
            # Create meal plan record
            plan_items = []
            for day_plan in plan_data.get("plan", []):
                for item in day_plan.get("items", []):
                    plan_items.append({
                        "day": day_plan["day"],
                        "product_name": item.get("name", ""),
                        "unit_price": float(item.get("price", 0)),
                        "quantity": 1,
                        "category": item.get("category", "general")
                    })
            
            meal_plan_data = {
                "id": None,  # Will be auto-generated
                "hijo_id": uid,
                "identificacion_padre": parent_id,
                "nombre_estudiante": student_name,
                "week_start": week_start,
                "budget": float(budget),
                "allergens": allergens or [],
                "preferences": preferences or [],
                "items": plan_items,
                "weekly_total": float(plan_data.get("weekly_total", 0)),
                "status": "active",
                "created_at": datetime.now(timezone.utc).isoformat(),
                "ai_generated": True,
            }
            
            # Save to database
            saved_plan = await self._save_meal_plan(meal_plan_data)
            
            return {
                "success": True,
                "plan": saved_plan,
                "ai_suggestions": plan_data.get("suggestions", ""),
                "budget_met": plan_data.get("budget_met", False),
                "weekly_total": plan_data.get("weekly_total", 0),
            }
            
        except Exception as e:
            logger.error(f"Error creating meal plan: {e}")
            return {"error": str(e)}
    
    async def get_weekly_plan(self, plan_id: str) -> Optional[Dict]:
        """Get a specific meal plan by ID."""
        return await plan_repo.get_meal_plan(plan_id)
    
    async def get_active_plan(self, parent_id: str) -> Optional[Dict]:
        """Get the active meal plan for a parent's student."""
        students = await get_parent_students(parent_id)
        if not students:
            return None
        
        student = students[0]
        return await plan_repo.get_active_plan_for_hijo(student["usuario_identificacion"])
    
    async def track_plan_compliance(self, plan_id: str) -> Dict:
        """
        Track actual consumption against the meal plan.
        Called daily to update compliance metrics.
        """
        try:
            plan = await plan_repo.get_meal_plan(plan_id)
            if not plan:
                return {"error": "Plan no encontrado"}
            
            uid = plan["hijo_id"]
            week_start = plan["week_start"]
            budget = float(plan.get("budget", 0))
            
            # Get actual consumption for the week
            actual_query = """
                SELECT 
                    nombre_producto,
                    CAST(precio AS INTEGER) as precio,
                    CAST(cantidad AS INTEGER) as cantidad,
                    DATE(fecha) as fecha
                FROM hackaton_ventas
                WHERE usuario_identificacion = $1 
                  AND DATE(fecha) >= $2
                  AND DATE(fecha) <= $2 + INTERVAL '5 days'
                ORDER BY fecha
            """
            
            actual_consumption = await fetch_all(actual_query, uid, week_start)
            
            # Calculate totals
            actual_total = sum(
                int(c["precio"]) * int(c["cantidad"]) 
                for c in actual_consumption
            )
            
            # Get planned items
            planned_items = plan.get("items", [])
            planned_total = sum(
                float(item.get("unit_price", 0)) * int(item.get("quantity", 1))
                for item in planned_items
            )
            
            # Calculate compliance
            if budget > 0:
                budget_compliance = 1 - abs(actual_total - budget) / budget
            else:
                budget_compliance = 1.0 if actual_total == 0 else 0.0
            
            # Item-level compliance (how many planned items were actually purchased)
            planned_names = {item["product_name"].lower() for item in planned_items}
            actual_names = {c["nombre_producto"].lower() for c in actual_consumption}
            
            if planned_names:
                item_compliance = len(planned_names & actual_names) / len(planned_names)
            else:
                item_compliance = 1.0
            
            # Overall compliance
            overall_compliance = (budget_compliance * 0.6 + item_compliance * 0.4)
            
            # Check if reward is earned
            reward_earned = overall_compliance >= self.REWARD_COMPLIANCE_THRESHOLD
            
            # Generate feedback
            feedback_data = {
                "budget": budget,
                "planned_total": planned_total,
                "actual_total": actual_total,
                "compliance": overall_compliance,
                "reward_earned": reward_earned
            }
            
            # Update plan with tracking data
            updates = {
                "actual_total": actual_total,
                "compliance_pct": round(overall_compliance * 100, 2),
                "reward_earned": reward_earned,
                "last_tracked": datetime.now(timezone.utc).isoformat(),
                "tracking_data": feedback_data
            }
            
            await plan_repo.update_meal_plan(plan_id, updates)
            
            return {
                "plan_id": plan_id,
                "budget": budget,
                "actual_total": actual_total,
                "planned_total": planned_total,
                "compliance_pct": round(overall_compliance * 100, 2),
                "budget_compliance": round(budget_compliance * 100, 2),
                "item_compliance": round(item_compliance * 100, 2),
                "reward_earned": reward_earned,
                "reward_message": self._get_reward_message(reward_earned, overall_compliance),
            }
            
        except Exception as e:
            logger.error(f"Error tracking plan compliance: {e}")
            return {"error": str(e)}
    
    async def apply_reward(self, plan_id: str) -> Dict:
        """
        Apply reward (discount) for successful plan completion.
        """
        try:
            plan = await plan_repo.get_meal_plan(plan_id)
            if not plan:
                return {"error": "Plan no encontrado"}
            
            if not plan.get("reward_earned", False):
                return {
                    "success": False,
                    "message": "No se cumplió el umbral para recompensa (90% compliance requerido)"
                }
            
            if plan.get("reward_applied", False):
                return {
                    "success": False,
                    "message": "La recompensa ya fue aplicada"
                }
            
            parent_id = plan["identificacion_padre"]
            discount_pct = self.REWARD_DISCOUNT_PCT
            
            # Create a discount code or apply to next package
            # For now, we'll create a notification and update the plan
            updates = {
                "reward_applied": True,
                "reward_discount_pct": discount_pct,
                "reward_applied_at": datetime.now(timezone.utc).isoformat(),
            }
            
            await plan_repo.update_meal_plan(plan_id, updates)
            
            # Send notification to parent
            from backend.services.notification_service import get_notification_service
            notif_service = get_notification_service()
            
            students = await get_parent_students(parent_id)
            student_name = students[0].get("nombre_estudiante", "el estudiante") if students else "el estudiante"
            
            message = (
                f"🎉 *¡Felicidades!* BioAlert+\n\n"
                f"¡Cumpliste con tu plan de alimentación semanal!\n"
                f"🏆 Recompensa: {discount_pct}% de descuento en tu próxima recarga\n\n"
                f"{student_name} lo hizo excelente esta semana. ¡Sigue así!"
            )
            
            # Log the reward notification
            from modules.notifications.schemas import Notification
            from modules.notifications import service as notif_svc
            
            notif = Notification(
                kind="reward_earned",
                recipient_phone="",
                usuario_identificacion=plan["hijo_id"],
                identificacion_padre=parent_id,
                message=message,
                status="pending",
            )
            await notif_svc.send_text.__wrapped__(notif)
            
            return {
                "success": True,
                "discount_pct": discount_pct,
                "message": f"Recompensa del {discount_pct}% aplicada. Notificación enviada al padre."
            }
            
        except Exception as e:
            logger.error(f"Error applying reward: {e}")
            return {"error": str(e)}
    
    async def get_plan_suggestions(self, plan_id: str) -> Dict:
        """
        Get AI-powered suggestions for plan adjustment.
        """
        try:
            plan = await plan_repo.get_meal_plan(plan_id)
            if not plan:
                return {"error": "Plan no encontrado"}
            
            uid = plan["hijo_id"]
            budget = float(plan.get("budget", 0))
            
            # Get actual vs planned
            compliance_data = await self.track_plan_compliance(plan_id)
            
            actual_total = compliance_data.get("actual_total", 0)
            actual_items_count = compliance_data.get("item_compliance", 0)
            
            # Generate suggestions
            suggestions = []
            
            if actual_total > budget * 1.2:
                suggestions.append({
                    "type": "budget_warning",
                    "message": "Estás gastando más del presupuesto. Considera productos más económicos.",
                    "priority": "high"
                })
            elif actual_total < budget * 0.8:
                suggestions.append({
                    "type": "budget_surplus",
                    "message": "Tienes presupuesto disponible. Podrías añadir más variedad.",
                    "priority": "low"
                })
            
            if actual_items_count < 60:
                suggestions.append({
                    "type": "variety_low",
                    "message": "Poca variedad en las compras. Intenta diversificar más.",
                    "priority": "medium"
                })
            
            # Check if approaching reward threshold
            compliance = compliance_data.get("compliance_pct", 0)
            if 80 <= compliance < 90:
                suggestions.append({
                    "type": "reward_close",
                    "message": f"¡Casi logras la recompensa! Necesitas {90 - compliance:.0f}% más de cumplimiento.",
                    "priority": "high"
                })
            
            return {
                "plan_id": plan_id,
                "suggestions": suggestions,
                "compliance": compliance_data,
            }
            
        except Exception as e:
            logger.error(f"Error getting plan suggestions: {e}")
            return {"error": str(e)}
    
    async def list_plans_for_parent(self, parent_id: str, limit: int = 10) -> List[Dict]:
        """Get all meal plans for a parent."""
        return await plan_repo.list_meal_plans(None, limit)  # Will need to filter by parent
    
    async def get_plans_history(self, parent_id: str) -> Dict:
        """Get historical meal plans with performance metrics."""
        try:
            students = await get_parent_students(parent_id)
            if not students:
                return {"plans": [], "summary": {}}
            
            uid = students[0]["usuario_identificacion"]
            
            # Get all plans for this student
            plans = await plan_repo.list_meal_plans(uid, limit=20)
            
            # Calculate summary statistics
            total_plans = len(plans)
            completed_plans = [p for p in plans if p.get("status") == "completed"]
            rewarded_plans = [p for p in plans if p.get("reward_applied", False)]
            
            avg_compliance = 0
            if plans:
                compliance_values = [p.get("compliance_pct", 0) for p in plans]
                avg_compliance = sum(compliance_values) / len(compliance_values)
            
            return {
                "plans": plans,
                "summary": {
                    "total_plans": total_plans,
                    "completed_plans": len(completed_plans),
                    "rewarded_plans": len(rewarded_plans),
                    "avg_compliance_pct": round(avg_compliance, 2),
                    "total_rewards_earned": len(rewarded_plans),
                }
            }
            
        except Exception as e:
            logger.error(f"Error getting plans history: {e}")
            return {"error": str(e)}
    
    # Helper methods
    
    async def _get_available_products(self, nit_colegio: Optional[str] = None) -> List[Dict]:
        """Get available products from the cafeteria."""
        query = """
            SELECT 
                nombre_producto,
                AVG(CAST(precio AS INTEGER)) as avg_price,
                COUNT(*) as times_sold
            FROM hackaton_ventas
            WHERE fecha >= CURRENT_DATE - INTERVAL '30 days'
            GROUP BY nombre_producto
            ORDER BY times_sold DESC
            LIMIT 20
        """
        
        try:
            results = await fetch_all(query)
            return [
                {"name": r["nombre_producto"], "avg_price": float(r["avg_price"])}
                for r in results
            ]
        except Exception as e:
            logger.error(f"Error getting available products: {e}")
            return []
    
    def _get_next_monday(self) -> datetime:
        """Get the next Monday from today."""
        today = datetime.now(timezone.utc)
        days_until_monday = (7 - today.weekday()) % 7
        if days_until_monday == 0 and today.weekday() != 0:
            days_until_monday = 7
        return today + timedelta(days=days_until_monday)
    
    def _get_reward_message(self, earned: bool, compliance: float) -> str:
        """Generate a message about reward status."""
        if earned:
            return f"🎉 ¡Felicidades! Ganaste un {self.REWARD_DISCOUNT_PCT}% de descuento."
        elif compliance >= 0.8:
            return f"📈 ¡Casi lo logras! {int((0.9 - compliance) * 100)}% más para ganar recompensa."
        else:
            return "💪 Sigue intentando. Mejora tu cumplimiento para ganar recompensas."
    
    async def _save_meal_plan(self, plan_data: Dict) -> Dict:
        """Save meal plan to database."""
        return await plan_repo.insert_meal_plan(plan_data)
    
    async def complete_weekly_plan(self, plan_id: str) -> Dict:
        """Mark a weekly plan as completed and finalize metrics."""
        try:
            # Track final compliance
            tracking = await self.track_plan_compliance(plan_id)
            
            # Update status
            updates = {
                "status": "completed",
                "completed_at": datetime.now(timezone.utc).isoformat(),
            }
            
            await plan_repo.update_meal_plan(plan_id, updates)
            
            # Apply reward if earned
            if tracking.get("reward_earned", False):
                await self.apply_reward(plan_id)
            
            return {
                "success": True,
                "plan_id": plan_id,
                "final_compliance": tracking.get("compliance_pct", 0),
                "reward_earned": tracking.get("reward_earned", False),
            }
            
        except Exception as e:
            logger.error(f"Error completing plan: {e}")
            return {"error": str(e)}


# Singleton instance
_meal_planner_service: Optional[MealPlannerService] = None


def get_meal_planner_service() -> MealPlannerService:
    """Get the singleton MealPlannerService instance."""
    global _meal_planner_service
    if _meal_planner_service is None:
        _meal_planner_service = MealPlannerService()
    return _meal_planner_service