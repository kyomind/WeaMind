
# Copilot Coding Agent Instructions for WeaMind

## Project Architecture & Core Concepts
- This repository contains only the line-bot (FastAPI) module, which serves as the entry point for LINE users and collaborates with other microservices (wea-ai, wea-data).
- The architecture follows Domain-Driven Design (DDD) principles. Main directories:
  - `app/core`: Global configuration, database connection
  - `app/user`: User data models, CRUD API, validation
  - `app/line`: LINE webhook handling, AI interaction
  - `app/main.py`: FastAPI entry point, router registration
- Other microservices (wea-ai, wea-data) are not included in this repo and interact only via HTTP API.

## Key Development Workflows
- Run tests: `uv run pytest`
- Lint: `uv run ruff check .`
- Format code: `uv run ruff format .`
- Type check: `uv run pyright .`

## Important Conventions & Rules
- All API POST/PUT request bodies must be named `payload`.
- Every function must have a docstring, following the `.github/prompts/docstring.prompt.md` standard.
- pytest fixture naming:
  - For helper functions: use a verb prefix, e.g., `create_user`
  - For objects/values: use a noun, e.g., `user`
- Add comments to important logic to explain design intent.
- Commit messages should be concise, focused on the intent of the change, and avoid unnecessary details.

## Integrations & External Dependencies
- Main dependencies: FastAPI, Pydantic, SQLAlchemy, Alembic, pytest, Ruff, Pyright
- PostgreSQL is the default database; schema migrations are managed by Alembic
- LINE webhook requests must have signature verification
- wea-ai is only responsible for intent detection and schema; all data queries are handled directly by line-bot

## Reference Documents
- Architecture & technical decisions: `docs/Architecture.md`
- Directory structure: `docs/Tree.md`
- Todo & progress: `docs/Todo.md`
- Technical blog articles: `blogs/README.md`

---

> These instructions are specific to the WeaMind project. Please follow the above conventions and structure for development, refactoring, and debugging. If anything is unclear, refer to `docs/Architecture.md` and the source code as the primary references.
