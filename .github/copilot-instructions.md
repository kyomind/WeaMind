# WeaMind Coding Agent Instructions

## Project Overview
WeaMind delivers fast and intuitive weather query services through LINE Bot. This repository contains the line-bot (FastAPI) module that serves as the main user interface.

## Architecture
- **DDD Structure**: `app/core` (config, DB), `app/user`, `app/line` (LINE webhook), `app/weather`, `app/main.py`
- **Database**: PostgreSQL with Alembic migrations
- **Dependencies**: FastAPI, Pydantic, SQLAlchemy 2.0, pytest, Ruff(lint, format), Pyright

## Coding Standards
1. **Type Safety**: Always use type hints
2. **Documentation**: Every function needs a docstring (follow `.github/prompts/docstring-guidelines.prompt.md`)
3. **Comments**: Add comments for important logic to explain design intent

### Naming Conventions
- **API Router Functions**: Request body parameter must be named `payload`
- **Pytest Fixtures**:
  - Helper functions: verb prefix (e.g., `create_user`)
  - Objects/values: noun (e.g., `user`)
- **Git Branches**: Use feature branches for new features or bug fixes. e.g. `feature/location-settings`(noun)

### Git Commit Messages
- **Natural English**: Use clear, descriptive English sentences
- **Examples**:
  - "Update CHANGELOG for v0.1.3"
  - "Enhance GitHub Actions release with full git history"
  - "Add location settings feature"

## References
- Architecture: `docs/Architecture.md` (high-level overview of the system architecture)
- Todo: `docs/Todo.md` (includes completed and pending tasks)
- Directory structure: `docs/Tree.md`
- PRD documents: `prd/` (internal only)
- Makefile: `Makefile` (project-specific shortcuts and preferred commands)
- CLI Best Practices: `.github/prompts/cli-best-practices.prompt.md` (guidelines for using terminal tools effectively)
- Docstring Guidelines: `.github/prompts/docstring-guidelines.prompt.md` (Python function documentation standards)
- Testing Guidelines: `.github/instructions/testing-guidelines.instructions.md` (comprehensive testing best practices and patterns)
- CHANGELOG Guide: `.github/instructions/changelog.instructions.md` (comprehensive guide for maintaining version history with AI assistance)

## Core Development Commands
- Tests: Use `runTests` tool in VS Code (preferred), or `uv run pytest` in terminal
- Coverage: `uv run pytest --cov=app --cov-report=xml --cov-report=html` to generate reports
- Lint: `uv run ruff check .`
- Format: `uv run ruff format .`
- Type check: `uv run pyright .`

## VS Code Environment Best Practices
*Note: Some tools mentioned below are GitHub Copilot specific. Use terminal alternatives if tools are unavailable.*
- **Testing**: Always use `runTests` tool for better integration with VS Code test explorer
- **Test Failures**: Use `test_failure` tool to get detailed failure information
- **File Errors**: Use `get_errors` tool for compile/lint errors in specific files
