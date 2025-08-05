
# Copilot Coding Agent Instructions for WeaMind

## Project Architecture & Core Concepts
- This repository contains only the line-bot (FastAPI) module, which serves as the entry point for LINE users and collaborates with other microservices (wea-ai, wea-data).
- The architecture follows Domain-Driven Design (DDD) principles. Main directories:
  - `app/core`: Global configuration, database connection
  - `app/user`: User data models, CRUD API, validation
  - `app/line`: LINE webhook handling
  - `app/main.py`: FastAPI entry point, router registration
- Other microservices (wea-ai, wea-data) are not included in this repo and interact only via HTTP API.

## Key Development Workflows
- Run tests: `uv run pytest`
- Lint: `uv run ruff check .`
- Format code: `uv run ruff format .`
- Type check: `uv run pyright .`

## Important Conventions & Rules
- All API request bodies must be named `payload`.
- Every function must have a docstring, following the `.github/prompts/docstring.prompt.md` standard.
- pytest fixture naming:
  - For helper functions: use a verb prefix, e.g., `create_user`
  - For objects/values: use a noun, e.g., `user`
- Add comments to important logic to explain design intent.
- Commit messages should be concise, focused on the intent of the change, and avoid unnecessary details.

## Integrations & External Dependencies
- Main dependencies: FastAPI, Pydantic, SQLAlchemy, Alembic, pytest, Ruff, Pyright
- PostgreSQL is the default database; schema migrations are managed by Alembic

## Reference Documents
- Product Requirements Documents (PRD): `prd/`, for internal reference only and not committed to the public repo.
- Other documentation: `docs/`.
