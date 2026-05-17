"""BioAlert+ FastAPI application entrypoint."""
import os
import logging
from pathlib import Path
from contextlib import asynccontextmanager
from fastapi import FastAPI, APIRouter
from dotenv import load_dotenv
from starlette.middleware.cors import CORSMiddleware

ROOT_DIR = Path(__file__).parent
load_dotenv(ROOT_DIR / ".env")

from core.sqlite import init_sqlite, close_sqlite  # noqa: E402
from core.postgres import close_pool  # noqa: E402

# Existing module routers
from modules.statistics.routes import router as statistics_router  # noqa: E402
from modules.planifications.routes import router as planifications_router  # noqa: E402
from modules.discounts.routes import router as discounts_router  # noqa: E402
from modules.feedback.routes import router as feedback_router  # noqa: E402
from modules.recommendations.routes import router as recommendations_router  # noqa: E402
from modules.notifications.routes import router as notifications_router  # noqa: E402
from modules.hijos.routes import router as hijos_router  # noqa: E402
from modules.approvals.routes import router as approvals_router  # noqa: E402

# New BioAlert+ feature routers
from handlers.whatsapp_handler import router as webhook_router  # noqa: E402
from api.bot_routes import router as bot_router  # noqa: E402
from api.recommendations_routes import router as ai_recommendations_router  # noqa: E402
from api.notifications_routes import router as auto_notifications_router  # noqa: E402

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger("bioalert")


async def _background_triggers():
    """Schedulers del pitch: saldo bajo, ratings, aprobaciones Gemini, viernes."""
    import asyncio
    from datetime import datetime

    from modules.notifications import service as notif_svc
    from modules.approvals import service as approval_svc

    last_noon = None
    last_friday = None
    while True:
        try:
            await asyncio.sleep(900)
            await notif_svc._send_low_balance_alerts()
            await notif_svc._send_consumption_rating_requests(minutes=30)
            await approval_svc.process_expired(limit=20)
            now = datetime.now()
            noon_key = now.strftime("%Y-%m-%d-12")
            if now.hour == 12 and last_noon != noon_key:
                last_noon = noon_key
                await notif_svc._send_no_consumption_alerts()
            friday_key = now.strftime("%Y-%m-%d-Fri16")
            if now.weekday() == 4 and now.hour == 16 and last_friday != friday_key:
                last_friday = friday_key
                await notif_svc._send_weekly_nutrition_report()
        except asyncio.CancelledError:
            break
        except Exception as e:
            logger.error("background trigger loop error: %s", e)


@asynccontextmanager
async def lifespan(app: FastAPI):
    import asyncio

    logger.info("BioAlert+ starting up")
    await init_sqlite()
    trigger_task = asyncio.create_task(_background_triggers())
    yield
    trigger_task.cancel()
    try:
        await trigger_task
    except asyncio.CancelledError:
        pass
    logger.info("BioAlert+ shutting down")
    await close_pool()
    await close_sqlite()


app = FastAPI(title="BioAlert+", lifespan=lifespan)

api_router = APIRouter(prefix="/api")


@api_router.get("/")
async def root():
    return {"name": "BioAlert+", "status": "ok"}


@api_router.get("/health")
async def health():
    return {"status": "healthy"}


api_router.include_router(statistics_router)
api_router.include_router(planifications_router)
api_router.include_router(discounts_router)
api_router.include_router(feedback_router)
api_router.include_router(recommendations_router)
api_router.include_router(notifications_router)
api_router.include_router(hijos_router)
api_router.include_router(approvals_router)

# BioAlert+ new feature routers
api_router.include_router(bot_router)
api_router.include_router(ai_recommendations_router)
api_router.include_router(auto_notifications_router)

app.include_router(api_router)

# Webhook router (outside /api prefix for Twilio compatibility)
app.include_router(webhook_router)

app.add_middleware(
    CORSMiddleware,
    allow_credentials=True,
    allow_origins=os.environ.get("CORS_ORIGINS", "*").split(","),
    allow_methods=["*"],
    allow_headers=["*"],
)
