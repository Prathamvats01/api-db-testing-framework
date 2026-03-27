# API + DB Testing Framework

> **`pytest src/tests/api/` works immediately — no setup needed.**
> For DB tests: `docker-compose up -d` then `pytest src/tests/db/`

[![CI](https://github.com/prathamvats/api-db-testing-framework/actions/workflows/ci.yml/badge.svg)](https://github.com/prathamvats/api-db-testing-framework/actions)
![Python](https://img.shields.io/badge/Python-3.11-3776AB?logo=python)
![Pytest](https://img.shields.io/badge/Pytest-8.1-0A9EDC?logo=pytest)
![PostgreSQL](https://img.shields.io/badge/PostgreSQL-15-336791?logo=postgresql)
![Docker](https://img.shields.io/badge/Docker-Compose-2496ED?logo=docker)
![Allure](https://img.shields.io/badge/Allure-Reports-orange)

---

## Architecture

```
├── config/
│   └── config.py               — Central config (env vars > .env > defaults)
├── contracts/
│   └── schemas.json            — JSON Schema contracts for all API responses
├── docker/
│   └── init.sql                — PostgreSQL seed: 4 tables, 50+ rows of data
├── src/
│   ├── api/
│   │   ├── clients/
│   │   │   ├── base_client.py      — HTTP session + retry + Allure logging
│   │   │   └── resource_clients.py — UsersClient, PostsClient, TodosClient
│   │   └── validators/
│   │       └── response_validator.py — Fluent assertion chain for responses
│   ├── db/
│   │   ├── connector/
│   │   │   └── db_connector.py     — SQLAlchemy connection pool + DataFrame queries
│   │   └── checks/
│   │       └── db_validator.py     — Row count, null, unique, FK, email, range checks
│   └── tests/
│       ├── api/
│       │   ├── test_users_api.py   — 14 API tests
│       │   └── test_posts_api.py   — 14 API tests
│       ├── db/
│       │   └── test_db_quality.py  — 20 DB quality checks
│       └── integration/
│           └── test_api_db_sync.py — 6 cross-layer consistency tests
├── conftest.py                 — All pytest fixtures (session/function scoped)
├── docker-compose.yml          — One command: PostgreSQL + auto-seed
└── pyproject.toml              — Pytest + Ruff + Black + MyPy config
```

---

## Quick Start

### API tests — zero setup, runs now
```bash
git clone https://github.com/prathamvats/api-db-testing-framework
cd api-db-testing-framework

python3 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt

# Run smoke suite (API only — no Docker needed)
pytest src/tests/api/ -m smoke -v

# Run full API regression
pytest src/tests/api/ -v

# Open Allure report
allure serve reports/allure-results
```

### DB + Integration tests — Docker required
```bash
# Start PostgreSQL and auto-seed the database (one command)
docker-compose up -d

# Run DB quality checks
pytest src/tests/db/ -v

# Run integration tests (API + DB cross-layer)
pytest src/tests/integration/ -v

# Run everything
pytest -v

# Stop database when done
docker-compose down
```

---

## Test Suite — 54 Tests

| Module          | Tests | Targets                        |
|-----------------|-------|--------------------------------|
| Users API       | 14    | JSONPlaceholder /users         |
| Posts API       | 14    | JSONPlaceholder /posts         |
| DB Quality      | 20    | PostgreSQL (Docker)            |
| API ↔ DB Sync   | 6     | Cross-layer consistency        |

---

## Key Design Decisions

**Why JSONPlaceholder?** It's always live, always free, no auth needed,
and has realistic relational data (users → posts → comments). Perfect for
demonstrating API testing patterns without infrastructure complexity.

**Why Docker PostgreSQL?** One command spins up a fully seeded database.
No cloud account, no credentials, no manual setup. The `init.sql` mirrors
JSONPlaceholder's data model so integration tests make sense.

**Why SQLAlchemy + Pandas?** SQLAlchemy abstracts the DB engine (swap
`psycopg2` for `pymysql` with one config change). Pandas makes it trivial
to assert on aggregate data — `df["null_rate"] < 0.05` reads like
English.

**Why a fluent ResponseValidator?** Instead of writing 5 separate `assert`
statements per test, you chain: `.status_is(200).body_has_key("id").validate()`.
All failures are collected and reported together — you see every problem
in one run, not just the first failure.

---

## Reporting

```bash
# Allure interactive report
allure serve reports/allure-results

# Pytest HTML report
open reports/pytest-report.html
```
