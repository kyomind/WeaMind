---
description: "Manual workflow for diagnosing and fixing GitHub Actions failures"
---

# WeaMind GitHub Actions Failure Fix Guide

## Goal

Use this prompt when the user asks you to fix a failing GitHub Actions run for WeaMind. Diagnose the failure from the real log, make the smallest necessary change, verify it locally, and report the result. Do not set up automation or background monitoring.

## Rules

1. Use the most recent failed run unless the user gives a specific run URL or run ID.
2. Read the failed log before changing any file.
3. Change only files that are directly related to the failure.
4. Prefer a minimal fix over a refactor.
5. If the log does not show a clear root cause, stop and ask for more information.

## Workflow

1. Find the failed run.
	- If the user gave a GitHub Actions URL or run ID, use that run.
	- Otherwise run `gh run list --repo kyomind/WeaMind --limit 10 --status failure` and choose the newest failed run.
2. Read the failed log with `gh run view <run-id> --repo kyomind/WeaMind --log-failed`.
3. Identify the first real error and classify it as one of these:
	- dependency vulnerability scan
	- test failure
	- lint, format, or type-check failure
	- workflow configuration problem
	- transient external-service failure
4. Apply the smallest fix that matches the error class.
	- For dependency scan failures, update the locked dependency versions in `uv.lock` and the source constraint in `pyproject.toml` if needed.
	- For test failures, fix the code or the test data.
	- For lint, format, or type-check failures, fix the code style, imports, or types.
	- For workflow problems, edit only the relevant `.github/workflows/*.yml` file.
	- For transient external-service failures, confirm whether a rerun is enough before changing code.
5. Run the closest local check that matches the failure.
	- `uv run pytest`
	- `uv run ruff check .`
	- `uv run pyright .`
	- `uv run pip-audit --progress-spinner=off`
	Run only the checks that are relevant to the failure.
6. Report the result.

## Report Format

- Root cause:
- Files changed:
- Verification:
- Recommended next step:

## Common Commands

```bash
gh run list --repo kyomind/WeaMind --limit 10 --status failure
gh run view <run-id> --repo kyomind/WeaMind --log-failed
gh run view <run-id> --repo kyomind/WeaMind --json conclusion,headSha,jobs,workflowName,url
```
