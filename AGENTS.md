# WeaMind Coding Agent Instructions

## Project Overview
WeaMind delivers fast and intuitive weather query services through LINE Bot. This repository contains the line-bot (FastAPI) module that serves as the main user interface.

For architecture and directory structure, see `README.md` (developer highlights), `docs/Architecture.md`, and `docs/Tree.md`.

## Coding Standards
1. **Type Safety**: Always use type hints
2. **Documentation**: Every function needs a docstring (follow `.github/instructions/docstring-guidelines.instructions.md`)
3. **Comments**: Add comments for important logic to explain design intent

### Naming Conventions
- **API Router Functions**: Request body parameter must be named `payload`
- **Pytest Fixtures**:
  - Helper functions: verb prefix (e.g., `create_user`)
  - Objects/values: noun (e.g., `user`)
- **Git Branches**: Use feature branches for new features and bug fixes, e.g. `feature/location-settings` (noun). Docs, README, and other non-code edits go directly on `main`.

### Git Commit Messages
- **Natural English**: Use clear, descriptive English sentences
- **Examples**:
  - "Update CHANGELOG for v0.1.3"
  - "Enhance GitHub Actions release with full git history"
  - "Add location settings feature"

## References
- Prompt Index: `.github/prompts/index.md` — start here to find task-specific prompts. After adding/removing a prompt or changing its `description:`, run `make update-prompt-index` and commit the index with the change.
- Architecture: `docs/Architecture.md`
- Directory structure: `docs/Tree.md`
- Task tracking: GitHub Issues via `docs/agents/issue-tracker.md`; `docs/Todo.md` is historical context
- PRD documents: `prd/` (internal only)
- Makefile: `Makefile` (deployment workflows and project-specific shortcuts)
- Tool Usage Guidelines: `.github/instructions/tool-usage.instructions.md` (read before running commands)
- Docstring Guidelines: `.github/instructions/docstring-guidelines.instructions.md`
- Testing Guidelines: `.github/instructions/testing-guidelines.instructions.md`
- Release Workflow: `.github/prompts/release.prompt.md` (includes the required CHANGELOG approval gate)

## Scheduled Maintenance
- `~/Code/agent-scheduler` runs the `weamind-maintenance-codex` job every Saturday 02:00 (Asia/Taipei). It executes `.github/prompts/github-maintenance.prompt.md` unattended in this repo and may merge PRs, push commits, and rerun workflows.
- Before moving, renaming, or restructuring `github-maintenance.prompt.md`, check that the job still works; the job lives in another repository, so confirm with the user before changing it.

## Agent skills

### Issue tracker

Issues and specs live in GitHub Issues for `kyomind/WeaMind`. See `docs/agents/issue-tracker.md`.

### Triage labels

Use the five default triage labels. See `docs/agents/triage-labels.md`.

### Domain docs

Use a single-context layout: root `GLOSSARY.md` and `docs/adr/`. See `docs/agents/domain.md`.

## Core Development Commands
**Important**: This project uses uv for package and virtual environment management. Always use `uv run` prefix for Python commands.

- Tests: `uv run pytest`
- Coverage: `uv run pytest --cov=app --cov-report=xml --cov-report=html`
- Lint: `uv run ruff check .`
- Format: `uv run ruff format .`
- Type check: `uv run pyright .`
