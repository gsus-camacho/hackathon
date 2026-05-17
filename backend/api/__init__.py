"""BioAlert+ API routes package."""
from backend.api.bot_routes import router as bot_router
from backend.api.recommendations_routes import router as recommendations_router
from backend.api.notifications_routes import router as auto_notifications_router

__all__ = ["bot_router", "recommendations_router", "auto_notifications_router"]