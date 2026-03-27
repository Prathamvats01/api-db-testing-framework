"""
conftest.py — Shared pytest fixtures for the entire test suite.

Fixture scopes:
  session  → created once for the entire test run (DB connector, API clients)
  module   → created once per test file
  function → created fresh for each test (default)

The DB connector is session-scoped so we don't open a new connection pool
for every test. API clients are stateless so they're function-scoped
(cheap to create, avoids any shared-state bugs between tests).
"""

from __future__ import annotations

import json
import logging
from pathlib import Path

import pytest

from src.api.clients.resource_clients import UsersClient, PostsClient, TodosClient
from src.api.validators.response_validator import ResponseValidator
from src.db.connector.db_connector import DBConnector
from src.db.checks.db_validator import DBValidator

logger = logging.getLogger(__name__)


# ── Database fixtures ──────────────────────────────────────────────

@pytest.fixture(scope="session")
def db_connector() -> DBConnector:
    """
    Session-scoped DB connector — one connection pool for the full run.
    Pings DB on startup to fail fast if Docker isn't running.
    """
    connector = DBConnector.get_instance()
    if not connector.ping():
        pytest.skip(
            "PostgreSQL not reachable. Run: docker-compose up -d\n"
            "Then re-run the DB tests."
        )
    logger.info("✔ DB connection verified")
    yield connector
    connector.dispose()


@pytest.fixture(scope="function")
def db_validator(db_connector: DBConnector) -> DBValidator:
    """Function-scoped DB validator (uses session connector underneath)."""
    return DBValidator()


# ── API client fixtures ────────────────────────────────────────────

@pytest.fixture(scope="function")
def users_client() -> UsersClient:
    return UsersClient()


@pytest.fixture(scope="function")
def posts_client() -> PostsClient:
    return PostsClient()


@pytest.fixture(scope="function")
def todos_client() -> TodosClient:
    return TodosClient()


# ── Schema fixtures ────────────────────────────────────────────────

@pytest.fixture(scope="session")
def schemas() -> dict:
    """Load all JSON Schema contracts from contracts/schemas.json."""
    schema_path = Path(__file__).parent / "contracts" / "schemas.json"
    with schema_path.open() as f:
        return json.load(f)


@pytest.fixture(scope="session")
def user_schema(schemas: dict) -> dict:
    return schemas["user_schema"]


@pytest.fixture(scope="session")
def post_schema(schemas: dict) -> dict:
    return schemas["post_schema"]


@pytest.fixture(scope="session")
def comment_schema(schemas: dict) -> dict:
    return schemas["comment_schema"]


@pytest.fixture(scope="session")
def todo_schema(schemas: dict) -> dict:
    return schemas["todo_schema"]


# ── Test data fixtures ─────────────────────────────────────────────

@pytest.fixture(scope="function")
def new_post_payload() -> dict:
    return {
        "userId": 1,
        "title":  "Test post created by automation framework",
        "body":   "This post was created by the API testing framework during a test run.",
    }


@pytest.fixture(scope="function")
def new_todo_payload() -> dict:
    return {
        "userId":    1,
        "title":     "Automated test task",
        "completed": False,
    }


@pytest.fixture(scope="function")
def update_post_payload() -> dict:
    return {
        "id":     1,
        "userId": 1,
        "title":  "Updated post title",
        "body":   "Updated post body via PUT request",
    }


# ── Utility fixtures ───────────────────────────────────────────────

@pytest.fixture(scope="function")
def validator() -> type[ResponseValidator]:
    """Returns the ResponseValidator class (used as a factory in tests)."""
    return ResponseValidator
