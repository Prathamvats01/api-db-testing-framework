"""
db_connector.py — SQLAlchemy database connector with connection pooling.

Thread-safe, context-manager-friendly. All DB checks call this.
Credentials come from config.py which reads environment variables,
so CI/CD just injects DB_HOST, DB_USER, DB_PASSWORD — no file changes.
"""

from __future__ import annotations

import logging
from contextlib import contextmanager
from typing import Generator

import pandas as pd
from sqlalchemy import create_engine, text
from sqlalchemy.engine import Engine
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy.pool import QueuePool

from config.config import DBConfig

logger = logging.getLogger(__name__)


class DBConnector:
    """
    Database connector with connection pooling and health check.

    Usage:
        connector = DBConnector()
        with connector.connection() as conn:
            result = conn.execute(text("SELECT COUNT(*) FROM users"))

        # Or for DataFrames:
        df = connector.query_to_df("SELECT * FROM users")
    """

    _instance: DBConnector | None = None

    def __init__(self) -> None:
        self._engine = self._build_engine()
        self._Session = sessionmaker(bind=self._engine)
        logger.info(
            "DBConnector ready | host=%s:%s | db=%s",
            DBConfig.HOST, DBConfig.PORT, DBConfig.NAME
        )

    @classmethod
    def get_instance(cls) -> "DBConnector":
        """Singleton — reuse one engine across tests for connection efficiency."""
        if cls._instance is None:
            cls._instance = DBConnector()
        return cls._instance

    # ─────────────────────────────────────────────────────────────
    #  Public API
    # ─────────────────────────────────────────────────────────────

    @contextmanager
    def connection(self) -> Generator:
        """Context manager yielding a raw SQLAlchemy connection."""
        with self._engine.connect() as conn:
            yield conn

    @contextmanager
    def session(self) -> Generator[Session, None, None]:
        """Context manager yielding an ORM session with auto-commit/rollback."""
        db_session = self._Session()
        try:
            yield db_session
            db_session.commit()
        except Exception:
            db_session.rollback()
            raise
        finally:
            db_session.close()

    def execute(self, sql: str, params: dict | None = None) -> list[dict]:
        """Execute a query and return results as list of dicts."""
        with self.connection() as conn:
            result = conn.execute(text(sql), params or {})
            return [dict(row._mapping) for row in result.fetchall()]

    def execute_scalar(self, sql: str, params: dict | None = None) -> int | float | str | None:
        """Execute a query and return the first column of the first row."""
        with self.connection() as conn:
            result = conn.execute(text(sql), params or {})
            row = result.fetchone()
            return row[0] if row else None

    def query_to_df(self, sql: str, params: dict | None = None) -> pd.DataFrame:
        """Execute a query and return results as a Pandas DataFrame."""
        with self.connection() as conn:
            return pd.read_sql(text(sql), conn, params=params or {})

    def get_row_count(self, table: str) -> int:
        """Returns row count for a table without loading data into memory."""
        result = self.execute_scalar(f"SELECT COUNT(*) FROM {table}")  # noqa: S608
        return int(result or 0)

    def table_exists(self, table: str) -> bool:
        """Returns True if the table exists in the database."""
        from sqlalchemy import inspect
        inspector = inspect(self._engine)
        return table in inspector.get_table_names()

    def get_column_names(self, table: str) -> list[str]:
        """Returns list of column names for a table."""
        from sqlalchemy import inspect
        inspector = inspect(self._engine)
        return [col["name"] for col in inspector.get_columns(table)]

    def ping(self) -> bool:
        """Test connectivity. Returns True on success."""
        try:
            with self.connection() as conn:
                conn.execute(text("SELECT 1"))
            return True
        except SQLAlchemyError as e:
            logger.error("Database ping failed: %s", e)
            return False

    def dispose(self) -> None:
        """Close all connections in the pool. Call during test teardown."""
        self._engine.dispose()
        DBConnector._instance = None
        logger.info("DB connection pool disposed")

    # ─────────────────────────────────────────────────────────────
    #  Private
    # ─────────────────────────────────────────────────────────────

    def _build_engine(self) -> Engine:
        return create_engine(
            DBConfig.connection_url(),
            poolclass=QueuePool,
            pool_size=DBConfig.POOL_SIZE,
            max_overflow=10,
            pool_pre_ping=True,       # verify connections before use
            pool_recycle=3600,        # recycle after 1 hour
            echo=False,
        )
