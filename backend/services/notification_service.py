"""Notification service - Automated alerts and notifications."""
import logging
from typing import Optional, Dict, List, Any
from datetime import datetime, timezone, timedelta
from core.postgres import fetch_all, fetch_one
from integrations.twilio_client import send_whatsapp_text
from modules.notifications.schemas import Notification
from modules.notifications import service as notif_svc
from modules.recommendations import service as rec_svc
from modules.planifications import service as plan_svc
from backend.services.parent_resolver import resolve_parent_by_phone, get_parent_students

logger = logging.getLogger(__name__)


class NotificationService:
    """Handles automated notifications for BioAlert+."""
    
    # Notification type constants
    ALLERGEN_ALERT = "allergen_alert"
    LOW_BALANCE = "low_balance"
    NO_CONSUMPTION = "no_consumption"
    WEEKLY_REPORT = "weekly_report"
    PACKAGE_OFFER = "package_offer"
    
    async def check_allergen_alerts(self) -> List[Dict]:
        """
        Check for recent allergen risks in transactions.
        Poll every 60 seconds for new sales that match student allergens.
        """
        alerts_sent = []
        
        try:
            # Get recent transactions (last 5 minutes)
            query = """
                SELECT DISTINCT usuario_identificacion, nombre_producto, 
                       nombre_estudiante, fecha, precio, cantidad
                FROM hackaton_ventas
                WHERE fecha >= NOW() - INTERVAL '5 minutes'
                ORDER BY fecha DESC
            """
            recent_sales = await fetch_all(query)
            
            for sale in recent_sales:
                uid = sale["usuario_identificacion"]
                product = sale["nombre_producto"]
                student_name = sale.get("nombre_estudiante", uid)
                
                # Check for allergen match
                matched_allergens = await rec_svc.check_allergen_risk(uid, product)
                
                if matched_allergens:
                    # Get parent phone
                    parent_id = await self._get_parent_for_student(uid)
                    if not parent_id:
                        logger.warning(f"No parent found for student {uid}")
                        continue
                    
                    parent_info = await self._get_parent_phone(parent_id)
                    if not parent_info:
                        continue
                    
                    phone = parent_info.get("telefono") or parent_info.get("whatsapp")
                    parent_name = parent_info.get("nombre_padre", "Padre/Madre")
                    
                    # Check if alert already sent recently
                    if await self._recent_alert_sent(uid, product, self.ALLERGEN_ALERT, minutes=30):
                        continue
                    
                    # Send alert
                    body = (
                        f"⚠️ *ALERTA ALERGENO - BioAlert+*\n\n"
                        f"{parent_name}, detectamos que {student_name} consumió:\n"
                        f"🔸 Producto: {product}\n"
                        f"🔸 Alérgenos: {', '.join(matched_allergens)}\n\n"
                        f"Por favor, verifica el estado de tu hijo y toma acciones preventivas."
                    )
                    
                    try:
                        resp = send_whatsapp_text(phone, body)
                        await self._log_notification(
                            parent_id=parent_id,
                            student_id=uid,
                            kind=self.ALLERGEN_ALERT,
                            message=body,
                            twilio_sid=resp.get("sid", ""),
                            status=resp.get("status", "sent")
                        )
                        alerts_sent.append({
                            "student": student_name,
                            "product": product,
                            "allergens": matched_allergens,
                            "status": "sent"
                        })
                        logger.info(f"Allergen alert sent: {student_name} - {product}")
                    except Exception as e:
                        logger.error(f"Failed to send allergen alert: {e}")
                        
        except Exception as e:
            logger.error(f"Error checking allergen alerts: {e}")
        
        return alerts_sent
    
    async def check_low_balance(self) -> List[Dict]:
        """
        Check for students with low balance.
        Runs every 15 minutes.
        """
        alerts_sent = []
        
        try:
            # Get students at risk
            at_risk = await plan_svc.students_at_risk(limit=50)
            
            for student in at_risk:
                uid = student["usuario_identificacion"]
                name = student.get("nombre_estudiante", uid)
                balance = student["current_balance"]
                days = student["days_remaining"]
                risk = student["risk_level"]
                
                # Only alert if high risk and days < 2
                if risk != "high" or days >= 2:
                    continue
                
                # Get parent
                parent_id = await self._get_parent_for_student(uid)
                if not parent_id:
                    continue
                
                parent_info = await self._get_parent_phone(parent_id)
                if not parent_info:
                    continue
                
                phone = parent_info.get("telefono") or parent_info.get("whatsapp")
                parent_name = parent_info.get("nombre_padre", "Padre/Madre")
                
                # Check if alert sent recently (avoid spam)
                if await self._recent_alert_sent(uid, None, self.LOW_BALANCE, hours=24):
                    continue
                
                # Get package offers
                from modules.discounts import service as disc_svc
                pkgs = await disc_svc.list_packages()
                best_pkg = pkgs[0] if pkgs else None
                
                body = (
                    f"🔔 *BioAlert+ — Saldo Bajo*\n\n"
                    f"Hola {parent_name}, el saldo de {name} está por agotarse:\n"
                    f"💰 Saldo actual: ${balance:,.0f}\n"
                    f"⏱️ Duración estimada: ~{days} días\n\n"
                )
                
                if best_pkg:
                    body += (
                        f"📦 Te recomendamos:\n"
                        f"{best_pkg['name']} - ${best_pkg['discounted_total']:,.0f} "
                        f"({best_pkg['discount_pct']}% descuento)\n\n"
                        f"Responde 'PAQUETE' para más información."
                    )
                else:
                    body += "Recarga pronto para evitar interrupciones."
                
                try:
                    resp = send_whatsapp_text(phone, body)
                    await self._log_notification(
                        parent_id=parent_id,
                        student_id=uid,
                        kind=self.LOW_BALANCE,
                        message=body,
                        twilio_sid=resp.get("sid", ""),
                        status=resp.get("status", "sent")
                    )
                    alerts_sent.append({
                        "student": name,
                        "balance": balance,
                        "days": days,
                        "status": "sent"
                    })
                except Exception as e:
                    logger.error(f"Failed to send low balance alert: {e}")
                    
        except Exception as e:
            logger.error(f"Error checking low balance: {e}")
        
        return alerts_sent
    
    async def check_no_consumption(self) -> List[Dict]:
        """
        Check for students with no consumption today.
        Runs at 12 PM daily.
        """
        alerts_sent = []
        
        try:
            # Get active students (had consumption in last 7 days)
            query = """
                SELECT DISTINCT usuario_identificacion, nombre_estudiante, 
                       identificacion_padre
                FROM hackaton_ventas
                WHERE fecha::date >= CURRENT_DATE - INTERVAL '7 days'
                  AND fecha::date < CURRENT_DATE
                ORDER BY nombre_estudiante
            """
            active_students = await fetch_all(query)
            
            for student in active_students:
                uid = student["usuario_identificacion"]
                name = student.get("nombre_estudiante", uid)
                parent_id = student.get("identificacion_padre")
                
                # Check if consumed today
                today_query = """
                    SELECT COUNT(*) as cnt FROM hackaton_ventas
                    WHERE usuario_identificacion = $1 AND DATE(fecha) = CURRENT_DATE
                """
                result = await fetch_one(today_query, uid)
                if result and int(result["cnt"]) > 0:
                    continue  # Already consumed today
                
                # Get parent phone
                if not parent_id:
                    parent_id = await self._get_parent_for_student(uid)
                
                if not parent_id:
                    continue
                
                parent_info = await self._get_parent_phone(parent_id)
                if not parent_info:
                    continue
                
                phone = parent_info.get("telefono") or parent_info.get("whatsapp")
                parent_name = parent_info.get("nombre_padre", "Padre/Madre")
                
                # Check if alert sent today
                if await self._recent_alert_sent(uid, None, self.NO_CONSUMPTION, hours=12):
                    continue
                
                body = (
                    f"🤔 *BioAlert+ — Ausencia de Consumo*\n\n"
                    f"Hola {parent_name},\n"
                    f"Notamos que {name} no registra compras en la cafetería hoy.\n\n"
                    f"¿Está todo bien? Si tu hijo llevó comida de casa, ¡perfecto! 🍱\n"
                    f"Si olvidó recargar, considera hacerlo para mañana."
                )
                
                try:
                    resp = send_whatsapp_text(phone, body)
                    await self._log_notification(
                        parent_id=parent_id,
                        student_id=uid,
                        kind=self.NO_CONSUMPTION,
                        message=body,
                        twilio_sid=resp.get("sid", ""),
                        status=resp.get("status", "sent")
                    )
                    alerts_sent.append({
                        "student": name,
                        "status": "sent"
                    })
                except Exception as e:
                    logger.error(f"Failed to send no consumption alert: {e}")
                    
        except Exception as e:
            logger.error(f"Error checking no consumption: {e}")
        
        return alerts_sent
    
    async def send_weekly_nutrition_report(self) -> List[Dict]:
        """
        Send weekly nutrition summary to parents.
        Runs Fridays at 5 PM.
        """
        reports_sent = []
        
        try:
            # Get all active parents with students
            query = """
                SELECT DISTINCT h.identificacion_padre, h.nombre_padre, 
                       h.telefono, h.whatsapp
                FROM hackaton_hijos h
                WHERE h.identificacion_padre IS NOT NULL
            """
            parents = await fetch_all(query)
            
            for parent in parents:
                parent_id = parent["identificacion_padre"]
                parent_name = parent.get("nombre_padre", "Padre/Madre")
                phone = parent.get("telefono") or parent.get("whatsapp")
                
                if not phone:
                    continue
                
                # Get students for this parent
                students = await get_parent_students(parent_id)
                if not students:
                    continue
                
                # Build weekly report for each student
                report_parts = []
                for student in students[:2]:  # Max 2 students per parent
                    uid = student["usuario_identificacion"]
                    name = student.get("nombre_estudiante", uid)
                    
                    # Get weekly consumption data
                    weekly_data = await self._get_weekly_consumption(uid)
                    if not weekly_data:
                        continue
                    
                    report_parts.append(
                        f"📊 *{name}* — Resumen Semanal\n"
                        f"• Días de consumo: {weekly_data['days']}\n"
                        f"• Total gastado: ${weekly_data['total']:,.0f}\n"
                        f"• Productos más comprados: {weekly_data['top_products']}\n"
                        f"• Promedio diario: ${weekly_data['daily_avg']:,.0f}"
                    )
                
                if not report_parts:
                    continue
                
                # Check if report sent this week
                if await self._recent_alert_sent(
                    parent_id, None, self.WEEKLY_REPORT, days=6
                ):
                    continue
                
                body = f"🌟 *BioAlert+ — Reporte Semanal*\n\nHola {parent_name},\n\n"
                body += "\n\n".join(report_parts)
                body += "\n\n¡Que tengas un excelente fin de semana! 🎉"
                
                try:
                    resp = send_whatsapp_text(phone, body)
                    await self._log_notification(
                        parent_id=parent_id,
                        student_id=None,
                        kind=self.WEEKLY_REPORT,
                        message=body,
                        twilio_sid=resp.get("sid", ""),
                        status=resp.get("status", "sent")
                    )
                    reports_sent.append({
                        "parent": parent_name,
                        "students": len(report_parts),
                        "status": "sent"
                    })
                except Exception as e:
                    logger.error(f"Failed to send weekly report: {e}")
                    
        except Exception as e:
            logger.error(f"Error sending weekly reports: {e}")
        
        return reports_sent
    
    # Helper methods
    
    async def _get_parent_for_student(self, uid: str) -> Optional[str]:
        """Get parent identification for a student."""
        query = """
            SELECT identificacion_padre FROM hackaton_hijos
            WHERE usuario_identificacion = $1
            LIMIT 1
        """
        result = await fetch_one(query, uid)
        return result["identificacion_padre"] if result else None
    
    async def _get_parent_phone(self, parent_id: str) -> Optional[Dict]:
        """Get phone contact for a parent."""
        query = """
            SELECT telefono, whatsapp, nombre_padre 
            FROM hackaton_padres_auth
            WHERE identificacion_padre = $1
            LIMIT 1
        """
        result = await fetch_one(query, parent_id)
        return dict(result) if result else None
    
    async def _get_weekly_consumption(self, uid: str) -> Optional[Dict]:
        """Get weekly consumption data for a student."""
        query = """
            SELECT 
                COUNT(DISTINCT DATE(fecha)) as days,
                SUM(CAST(precio AS INTEGER) * CAST(cantidad AS INTEGER)) as total,
                AVG(CAST(precio AS INTEGER) * CAST(cantidad AS INTEGER)) as daily_avg
            FROM hackaton_ventas
            WHERE usuario_identificacion = $1 
              AND fecha::date >= CURRENT_DATE - INTERVAL '7 days'
        """
        result = await fetch_one(query, uid)
        
        if not result or not result["total"]:
            return None
        
        # Get top products
        top_query = """
            SELECT nombre_producto, COUNT(*) as veces
            FROM hackaton_ventas
            WHERE usuario_identificacion = $1 
              AND fecha::date >= CURRENT_DATE - INTERVAL '7 days'
            GROUP BY nombre_producto
            ORDER BY veces DESC
            LIMIT 3
        """
        top_products = await fetch_all(top_query, uid)
        top_names = ", ".join([p["nombre_producto"] for p in top_products])
        
        return {
            "days": int(result["days"] or 0),
            "total": float(result["total"] or 0),
            "daily_avg": float(result["daily_avg"] or 0),
            "top_products": top_names or "N/A"
        }
    
    async def _recent_alert_sent(
        self, 
        student_id: Optional[str], 
        product: Optional[str], 
        kind: str, 
        hours: int = 0, 
        days: int = 0
    ) -> bool:
        """Check if a similar alert was sent recently."""
        total_hours = hours + (days * 24)
        if total_hours == 0:
            return False
        
        query = """
            SELECT COUNT(*) as cnt FROM notifications
            WHERE kind = $1 
              AND timestamp >= NOW() - INTERVAL '%s hours'
        """ % total_hours
        
        if student_id:
            query += f" AND usuario_identificacion = '{student_id}'"
        
        result = await fetch_one(query)
        return result and int(result["cnt"]) > 0
    
    async def _log_notification(
        self,
        parent_id: str,
        student_id: Optional[str],
        kind: str,
        message: str,
        twilio_sid: str,
        status: str
    ):
        """Log a notification to the database."""
        notif = Notification(
            kind=kind,
            recipient_phone="",
            usuario_identificacion=student_id,
            identificacion_padre=parent_id,
            message=message,
            twilio_sid=twilio_sid,
            status=status,
        )
        await notif_svc.send_text.__wrapped__(notif)  # Direct insert


# Singleton instance
_notification_service: Optional[NotificationService] = None


def get_notification_service() -> NotificationService:
    """Get the singleton NotificationService instance."""
    global _notification_service
    if _notification_service is None:
        _notification_service = NotificationService()
    return _notification_service