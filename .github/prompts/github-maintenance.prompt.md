---
description: "Manual workflow for triaging and fixing GitHub maintenance items"
---

# WeaMind GitHub Maintenance Triage Guide

## Goal

Use this prompt when the user asks you to check or fix WeaMind GitHub maintenance items. Triage the three common robot-driven surfaces: Dependabot PRs, failing GitHub Actions runs, and CodeQL or security alerts. Read the current GitHub state with `gh`, make the smallest necessary change, verify it locally when relevant, and report the result. Do not set up automation or background monitoring unless the user explicitly asks.

## Rules

1. Use `gh` CLI for all GitHub operations.
2. Check all three surfaces unless the user asks for only one:
	- open Dependabot PRs
	- failed GitHub Actions runs
	- open CodeQL or security alerts
3. Read the relevant PR, run log, or alert details before changing any file.
4. Change only files that are directly related to the item being handled.
5. Prefer a minimal fix over a refactor.
6. Do not merge or close anything until the relevant checks are current and passing.
7. If GitHub does not show a clear root cause or safe next action, stop and ask for more information.

## Workflow

1. Establish the current GitHub state.
	- List open Dependabot PRs:
		`gh pr list --repo kyomind/WeaMind --author app/dependabot --state open --json number,title,headRefName,baseRefName,mergeStateStatus,statusCheckRollup,url`
	- List recent failed runs:
		`gh run list --repo kyomind/WeaMind --limit 10 --status failure`
	- List open CodeQL alerts:
		`gh api "/repos/kyomind/WeaMind/code-scanning/alerts?state=open"`
	- List open Dependabot security alerts:
		`gh api "/repos/kyomind/WeaMind/dependabot/alerts?state=open"`
	- If the user gave a PR URL, run URL, run ID, or alert URL, prioritize that item but still mention whether the other surfaces were checked.
2. Classify each actionable item.
	- Dependabot dependency PR
	- Dependabot GitHub Actions PR
	- GitHub Actions failure
	- CodeQL alert
	- Dependabot security alert or dependency vulnerability scan failure
	- transient external-service failure
3. Handle Dependabot PRs.
	- Read the PR before changing or merging it:
		`gh pr view <pr-number> --repo kyomind/WeaMind --json title,body,author,files,commits,mergeStateStatus,statusCheckRollup,url`
	- For Python dependency PRs, confirm `pyproject.toml` and `uv.lock` are consistent. Do not merge a pyproject-only dependency bump when CI uses `uv sync --locked`.
	- For GitHub Actions PRs, inspect the changed workflow/action references and confirm the update is low risk.
	- If the branch is stale, update it before trusting old checks:
		`gh pr update-branch <pr-number> --repo kyomind/WeaMind --rebase`
	- Merge only low-risk PRs with current passing checks:
		`gh pr merge <pr-number> --repo kyomind/WeaMind --squash --delete-branch`
	- If checks fail, handle the failure using the GitHub Actions failure path below.
4. Handle GitHub Actions failures.
	- If the user gave a GitHub Actions URL or run ID, use that run.
	- Otherwise run `gh run list --repo kyomind/WeaMind --limit 10 --status failure` and choose the newest failed run.
	- Read the failed log with `gh run view <run-id> --repo kyomind/WeaMind --log-failed`.
	- Identify the first real error and classify it as one of these:
		- dependency vulnerability scan or stale `pip-audit` ignore
		- test failure
		- lint, format, type-check, or Bandit failure
		- workflow configuration problem
		- transient external-service failure
	- Apply the smallest fix that matches the error class.
	- For dependency scan failures, update the locked dependency versions in `uv.lock` and the source constraint in `pyproject.toml` if needed.
	- For stale `pip-audit` ignores, update the ignore list only after confirming the advisory status.
	- For test failures, fix the code or the test data.
	- For lint, format, type-check, or Bandit failures, fix the code style, imports, types, or flagged security issue.
	- For workflow problems, edit only the relevant `.github/workflows/*.yml` file.
	- For transient external-service failures, confirm whether a rerun is enough before changing code.
5. Handle CodeQL or security alerts.
	- Read alert details before changing code:
		`gh api /repos/kyomind/WeaMind/code-scanning/alerts/<alert-number>`
	- For Dependabot security alerts, read alert details before changing dependencies:
		`gh api /repos/kyomind/WeaMind/dependabot/alerts/<alert-number>`
	- For dependency security advisories, inspect the related Dependabot PR or use the dependency update path.
	- For CodeQL alerts, fix the vulnerable source or workflow pattern directly. If it is a false positive, document the reasoning and prefer a narrow code or workflow annotation over broad suppression.
	- For workflow security alerts, inspect `.github/workflows/*.yml` and keep privileged workflows restricted to trusted refs and events.
	- Do not dismiss security alerts unless the user explicitly asks and the false-positive reasoning is clear.
6. Run the closest local check that matches the item.
	- `uv run pytest`
	- `uv run ruff check .`
	- `uv run pyright .`
	- `uv run bandit -c bandit.yaml -r app`
	- `uv run pip-audit --progress-spinner=off`
	- `python3 scripts/check_pip_audit_ignores.py`
	Run only the checks that are relevant to the item.
7. Report the result.

## Report Format

- Checked:
- Action taken:
- Root cause:
- Files changed:
- Verification:
- Recommended next step:

## Common Commands

```bash
gh pr list --repo kyomind/WeaMind --author app/dependabot --state open --json number,title,headRefName,baseRefName,mergeStateStatus,statusCheckRollup,url
gh pr view <pr-number> --repo kyomind/WeaMind --json title,body,author,files,commits,mergeStateStatus,statusCheckRollup,url
gh pr checks <pr-number> --repo kyomind/WeaMind
gh pr update-branch <pr-number> --repo kyomind/WeaMind --rebase
gh pr merge <pr-number> --repo kyomind/WeaMind --squash --delete-branch
gh run list --repo kyomind/WeaMind --limit 10 --status failure
gh run view <run-id> --repo kyomind/WeaMind --log-failed
gh run view <run-id> --repo kyomind/WeaMind --json conclusion,headSha,jobs,workflowName,url
gh api "/repos/kyomind/WeaMind/code-scanning/alerts?state=open"
gh api /repos/kyomind/WeaMind/code-scanning/alerts/<alert-number>
gh api "/repos/kyomind/WeaMind/dependabot/alerts?state=open"
gh api /repos/kyomind/WeaMind/dependabot/alerts/<alert-number>
```
