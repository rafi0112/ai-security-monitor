"""
AI Security Monitor - FastAPI Backend
Main application entry point
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.trustedhost import TrustedHostMiddleware
from contextlib import asynccontextmanager
import logging

from app.api import auth, logs, alerts, stats, simulate
from app.core.config import settings
from app.core.database import init_db
from app.ml.detector import SecurityDetector
from app.services.log_monitor import LogMonitor

# ─── LOGGING SETUP ────────────────────────────────────────────────────────────
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    handlers=[
        logging.FileHandler("logs/app.log"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# ─── LIFESPAN (startup / shutdown) ────────────────────────────────────────────
@asynccontextmanager
async def lifespan(app: FastAPI):
    # STARTUP
    logger.info("🚀 AI Security Monitor starting up...")
    await init_db()

    # Initialize ML detector
    app.state.detector = SecurityDetector()
    await app.state.detector.train_initial_model()
    logger.info("✅ ML Detector initialized")

    # Start background log monitor
    app.state.log_monitor = LogMonitor(detector=app.state.detector)
    await app.state.log_monitor.start()
    logger.info("✅ Log Monitor started")

    yield

    # SHUTDOWN
    logger.info("🛑 Shutting down...")
    await app.state.log_monitor.stop()


# ─── APP FACTORY ──────────────────────────────────────────────────────────────
def create_app() -> FastAPI:
    app = FastAPI(
        title="AI Security Monitor",
        description="Real-time AI-powered security monitoring system",
        version="1.0.0",
        docs_url="/api/docs",
        redoc_url="/api/redoc",
        lifespan=lifespan,
    )

    # CORS — allow React dev server
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.CORS_ORIGINS,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # Register all routers
    app.include_router(auth.router,     prefix="/api/auth",     tags=["Auth"])
    app.include_router(logs.router,     prefix="/api/logs",     tags=["Logs"])
    app.include_router(alerts.router,   prefix="/api/alerts",   tags=["Alerts"])
    app.include_router(stats.router,    prefix="/api/stats",    tags=["Stats"])
    app.include_router(simulate.router, prefix="/api/simulate", tags=["Simulate"])

    @app.get("/api/health")
    async def health():
        return {"status": "ok", "service": "ai-security-monitor"}

    return app


app = create_app()
