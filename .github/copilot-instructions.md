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

## Version Release Guidelines
### CHANGELOG Management
- **Format**: Follow [Keep a Changelog](https://keepachangelog.com/) standard
- **Language**: Use Traditional Chinese (zh-TW) for user-facing content
- **Categories**: 新增(Added)/修正(Fixed)/改進(Changed)/移除(Removed)
- **Tone**: Professional yet approachable, emphasize user value and product benefits
- **Version Update Process**:
  1. Update `pyproject.toml` version field
  2. Update `CHANGELOG.md` with detailed changes (use AI assistance following `.github/instructions/changelog.instructions.md`)
  3. Commit with message: `chore: bump version to vX.Y.Z`
  4. Create and push git tag: `git tag vX.Y.Z && git push origin main --tags`

### AI-Assisted CHANGELOG Generation
When updating CHANGELOG, use Copilot Chat with this prompt template:
```
根據以下 git commits 為 WeaMind 產生 CHANGELOG 內容：
[git log output]

要求：繁體中文、Keep a Changelog 格式、突出產品價值、加入適當 emoji、保持專業親和語調
```
