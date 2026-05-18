"""
Core configuration — reads from .env or environment variables.
All defaults are safe for local development.
"""

from pydantic_settings import BaseSettings
from typing import List
import os


class Settings(BaseSettings):
    # ── App ───────────────────────────────────────────────────────────────────
    APP_NAME: str = "AI Security Monitor"
    DEBUG: bool = True
    SECRET_KEY: str = "CHANGE_ME_IN_PRODUCTION_USE_32+_RANDOM_CHARS"
    API_V1_STR: str = "/api"

    # ── CORS ──────────────────────────────────────────────────────────────────
    CORS_ORIGINS: List[str] = [
        "http://localhost:3000",   # React dev server
        "http://localhost:5173",   # Vite dev server
        "http://localhost:80",     # Nginx
    ]

    # ── Database (SQLite for Phase 1) ─────────────────────────────────────────
    DATABASE_URL: str = "sqlite+aiosqlite:///./data/security.db"

    # ── JWT Auth ──────────────────────────────────────────────────────────────
    JWT_ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60

    # ── Log Files ─────────────────────────────────────────────────────────────
    NGINX_LOG_PATH: str = "/var/log/nginx/access.log"
    APP_LOG_PATH: str = "logs/app.log"
    ATTACK_LOG_PATH: str = "logs/attacks.log"

    # ── ML Detection ──────────────────────────────────────────────────────────
    # Brute-force: how many failures in how many seconds = alert
    BRUTE_FORCE_THRESHOLD: int = 5
    BRUTE_FORCE_WINDOW_SECONDS: int = 60

    # Anomaly score threshold for IsolationForest (-1..0: more negative = more anomalous)
    ANOMALY_SCORE_THRESHOLD: float = -0.3

    # ── Rate Limiting ─────────────────────────────────────────────────────────
    RATE_LIMIT_REQUESTS: int = 100
    RATE_LIMIT_WINDOW_SECONDS: int = 60

    class Config:
        env_file = ".env"
        case_sensitive = True


settings = Settings()
