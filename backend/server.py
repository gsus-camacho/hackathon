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


@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("BioAlert+ starting up")
    await init_sqlite()
    yield
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
