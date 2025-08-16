# WeaMind Coding Agent Instructions

## Project Overview
WeaMind delivers intelligent weather services through AI-powered interactions. This repository contains only the line-bot (FastAPI) module that serves as the user entry point and collaborates with other microservices (wea-ai, wea-data) via HTTP APIs.

## Architecture
- **DDD Structure**: `app/core` (config, DB), `app/user`, `app/line` (LINE webhook), `app/weather`, `app/main.py`
- **Database**: PostgreSQL with Alembic migrations
- **Dependencies**: FastAPI, Pydantic, SQLAlchemy, pytest, Ruff, Pyright

## Coding Standards
1. **Type Safety**: Always use type hints
2. **Documentation**: Every function needs a docstring (follow `.github/prompts/docstring.prompt.md`)
3. **Comments**: Add comments for important logic to explain design intent
4. **Commit Messages**: Write concise, natural messages focusing on the overall intent of changes (under 10 words, avoid listing specific method names)

### Naming Conventions
- **API Router Functions**: Request body parameter must be named `payload`
- **Pytest Fixtures**:
  - Helper functions: verb prefix (e.g., `create_user`)
  - Objects/values: noun (e.g., `user`)
- **Git Branches**: Use feature branches for new features or bug fixes. e.g. `feature/location-settings`(noun)

## References
- Todo: `docs/Todo.md` (includes completed and pending tasks)
- Architecture: `docs/Architecture.md`
- Directory structure: `docs/Tree.md`
- PRD documents: `prd/` (internal only)
- Makefile: `Makefile`

## Development Commands
- Tests: `uv run pytest`
- Lint: `uv run ruff check .`
- Format: `uv run ruff format .`
- Type check: `uv run pyright .`
