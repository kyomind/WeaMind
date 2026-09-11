# WeaMind Coding Agent Instructions

## Project Overview
WeaMind delivers fast and intuitive weather query services through LINE Bot. This repository contains the line-bot (FastAPI) module that serves as the main user interface.

For architecture and directory structure, see `README.md` (developer highlights), `docs/Architecture.md`, and `docs/Tree.md`.

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
- Architecture: `docs/Architecture.md`
- Directory structure: `docs/Tree.md`
- Todo: `docs/Todo.md` (completed and pending tasks)
- PRD documents: `prd/` (internal only)
- Makefile: `Makefile` (deployment workflows and project-specific shortcuts)
- CLI Best Practices: `.github/prompts/cli-best-practices.prompt.md`
- Docstring Guidelines: `.github/prompts/docstring-guidelines.prompt.md`
- Testing Guidelines: `.github/instructions/testing-guidelines.instructions.md`
- CHANGELOG Guide: `.github/instructions/changelog.instructions.md`

## Core Development Commands
**Important**: This project uses uv for package and virtual environment management. Always use `uv run` prefix for Python commands.

- Tests: `uv run pytest`
- Coverage: `uv run pytest --cov=app --cov-report=xml --cov-report=html`
- Lint: `uv run ruff check .`
- Format: `uv run ruff format .`
- Type check: `uv run pyright .`

## AGENTS.md as the project main prompt

- Treat `AGENTS.md` as the project's sole main prompt.
- When main instruction-related changes are needed, edit `AGENTS.md` directly.
