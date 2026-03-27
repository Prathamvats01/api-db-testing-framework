"""
config.py — Central configuration for the API + DB testing framework.

Resolution order (highest priority first):
  1. Environment variables (injected by CI)
  2. .env file (local development)
  3. Default values hardcoded below

This means CI only needs to set env vars — no file changes needed.
"""

import os
from pathlib import Path
from dotenv import load_dotenv

# Load .env if it exists (local dev only — not committed to git)
_env_path = Path(__file__).parent.parent / ".env"
if _env_path.exists():
    load_dotenv(_env_path)


class APIConfig:
    """JSONPlaceholder API — always live, zero setup required."""

    BASE_URL:           str = os.getenv("API_BASE_URL", "https://jsonplaceholder.typicode.com")
    TIMEOUT_SECONDS:    int = int(os.getenv("API_TIMEOUT", "15"))
    MAX_RETRIES:        int = int(os.getenv("API_MAX_RETRIES", "3"))
    RETRY_BACKOFF:      float = float(os.getenv("API_RETRY_BACKOFF", "0.5"))

    # Performance thresholds (ms)
    RESPONSE_TIME_P1:   int = 2000   # Critical endpoints
    RESPONSE_TIME_P2:   int = 3000   # Standard endpoints
    RESPONSE_TIME_P3:   int = 5000   # Heavy/list endpoints


class DBConfig:
    """PostgreSQL — spun up by docker-compose, credentials match init.sql."""

    HOST:       str = os.getenv("DB_HOST",     "localhost")
    PORT:       int = int(os.getenv("DB_PORT", "5432"))
    NAME:       str = os.getenv("DB_NAME",     "testdb")
    USER:       str = os.getenv("DB_USER",     "testuser")
    PASSWORD:   str = os.getenv("DB_PASSWORD", "testpassword")
    POOL_SIZE:  int = int(os.getenv("DB_POOL_SIZE", "5"))

    @classmethod
    def connection_url(cls) -> str:
        return (
            f"postgresql+psycopg2://{cls.USER}:{cls.PASSWORD}"
            f"@{cls.HOST}:{cls.PORT}/{cls.NAME}"
        )


class ReportConfig:
    """Allure and HTML report paths."""

    ALLURE_RESULTS_DIR: str = "reports/allure-results"
    HTML_REPORT_PATH:   str = "reports/pytest-report.html"
    LOG_LEVEL:          str = os.getenv("LOG_LEVEL", "INFO")
