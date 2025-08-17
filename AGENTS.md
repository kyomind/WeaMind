# WeaMind Coding Agent Instructions

## Project Overview
WeaMind delivers fast and intuitive weather query services through LINE Bot. This repository contains the line-bot (FastAPI) module that serves as the main user interface.

## Architecture
- **DDD Structure**: `app/core` (config, DB), `app/user`, `app/line` (LINE webhook), `app/weather`, `app/main.py`
- **Database**: PostgreSQL with Alembic migrations
- **Dependencies**: FastAPI, Pydantic, SQLAlchemy 2.0, pytest, Ruff(lint, format), Pyright

## Coding Standards
1. **Type Safety**: Always use type hints
2. **Documentation**: Every function needs a docstring (follow `.github/prompts/docstring.prompt.md`)
3. **Comments**: Add comments for important logic to explain design intent

### Naming Conventions
- **API Router Functions**: Request body parameter must be named `payload`
- **Pytest Fixtures**:
  - Helper functions: verb prefix (e.g., `create_user`)
  - Objects/values: noun (e.g., `user`)
- **Git Branches**: Use feature branches for new features or bug fixes. e.g. `feature/location-settings`(noun)

## References
- Architecture: `docs/Architecture.md` (high-level overview of the system architecture)
- Todo: `docs/Todo.md` (includes completed and pending tasks)
- Directory structure: `docs/Tree.md`
- PRD documents: `prd/` (internal only)
- Makefile: `Makefile`(must read for CLI commands)

## Core Development Commands
- Tests: `uv run pytest`
- Lint: `uv run ruff check .`
- Format: `uv run ruff format .`
- Type check: `uv run pyright .`
