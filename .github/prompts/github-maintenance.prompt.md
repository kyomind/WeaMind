---
description: "Triage and fix WeaMind GitHub maintenance items"
---

# WeaMind GitHub Maintenance Guide

## Outcome

Use this prompt when the user asks you to check, triage, or fix WeaMind GitHub maintenance items. Produce a current maintenance snapshot, handle safe actionable items end to end, and clearly report what remains.

Always consider these three surfaces unless the user asks for a narrower scope:

- Dependabot PRs for Python dependencies and GitHub Actions
- failed GitHub Actions runs
- CodeQL code scanning alerts and Dependabot security alerts

Completion means you can say:

- which of the three surfaces were checked
- which items were actionable, stale, blocked, or already safe
- what you changed, merged, reran, or intentionally left alone
- what evidence supports the decision
- which local or GitHub checks confirm the result

Prefer practical maintenance: read the evidence, make the smallest useful change, verify the relevant path, and avoid broad refactors or background automation unless the user asks for them.

## Evidence Boundaries

- Use `gh` CLI for GitHub operations.
- Do not infer current GitHub state from old local notes, old failed runs, or stale PR checks. Recheck the live PR, run, or alert before acting.
- Read the relevant PR, run log, or alert details before changing files.
- Treat old failed runs as context only when a newer commit or rerun supersedes them.
- Do not merge PRs, rerun workflows, dismiss alerts, or close items unless the evidence makes that action safe.
- If the evidence does not show a clear root cause or safe next action, stop and ask for more information.

## Snapshot

Start with a compact snapshot unless the user gave a specific PR, run, or alert URL.

```bash
gh pr list --repo kyomind/WeaMind --author app/dependabot --state open --json number,title,headRefName,baseRefName,mergeStateStatus,statusCheckRollup,url
gh run list --repo kyomind/WeaMind --limit 10 --status failure
gh api "/repos/kyomind/WeaMind/code-scanning/alerts?state=open"
gh api "/repos/kyomind/WeaMind/dependabot/alerts?state=open"
```

If the user gave a specific URL or ID, prioritize it, but still mention whether the other surfaces were checked.

## Decision Rules

Classify each item by the action it needs:

- safe Dependabot dependency PR
- safe Dependabot GitHub Actions PR
- dependency PR that needs lockfile or constraint repair
- GitHub Actions failure with a reproducible root cause
- CodeQL or security alert that needs a code, dependency, or workflow fix
- transient or stale item that should be rerun, refreshed, or left alone
- blocked item that needs user input

Prioritize security alerts and currently failing required checks over routine version bumps. Batch low-risk Dependabot PRs when the evidence is clear, but avoid mixing unrelated code fixes into bot PR handling.

## Handle Items

### Dependabot

Inspect each PR before changing or merging it.

```bash
gh pr view <pr-number> --repo kyomind/WeaMind --json title,body,author,files,commits,mergeStateStatus,statusCheckRollup,url
gh pr checks <pr-number> --repo kyomind/WeaMind
```

Python dependency PRs must keep `pyproject.toml` and `uv.lock` consistent because CI uses `uv sync --locked`. Do not merge a pyproject-only bump with an outdated lockfile. If the fix is safe, repair the lockfile and rerun the relevant checks.

GitHub Actions PRs are usually safe when they only update action versions, the changed workflow still matches this repo's pinning/comment conventions, and fresh checks pass.

If the branch is stale, refresh it before trusting checks:

```bash
gh pr update-branch <pr-number> --repo kyomind/WeaMind --rebase
```

Merge only low-risk PRs with current passing checks:

```bash
gh pr merge <pr-number> --repo kyomind/WeaMind --squash --delete-branch
```

### GitHub Actions

Use the user-provided run when available. Otherwise choose the newest relevant failed run.

```bash
gh run view <run-id> --repo kyomind/WeaMind --log-failed
gh run view <run-id> --repo kyomind/WeaMind --json conclusion,headSha,jobs,workflowName,url
```

Identify the first real error and fix the narrowest cause:

- dependency vulnerability scan or stale `pip-audit` ignore
- test failure
- lint, format, type-check, or Bandit failure
- workflow configuration problem
- transient external-service failure

For transient failures, prefer rerun or clear reporting over code changes. For workflow configuration problems, edit only the relevant `.github/workflows/*.yml` file.

### Security

Read alert details before changing code or dependencies.

```bash
gh api /repos/kyomind/WeaMind/code-scanning/alerts/<alert-number>
gh api /repos/kyomind/WeaMind/dependabot/alerts/<alert-number>
```

For dependency security advisories, prefer the related Dependabot PR when one exists. If no PR exists or it is broken, update the dependency constraint and lockfile directly.

For CodeQL alerts, fix the vulnerable source or workflow pattern directly. If it appears to be a false positive, explain the reasoning and prefer a narrow code or workflow annotation over broad suppression. For workflow security alerts, keep privileged workflows restricted to trusted refs and events. Do not dismiss alerts unless the user explicitly asks.

## Verification

Run only checks that match the item you handled:

- `uv run pytest`
- `uv run ruff check .`
- `uv run pyright .`
- `uv run bandit -c bandit.yaml -r app`
- `uv run pip-audit --progress-spinner=off`
- `python3 scripts/check_pip_audit_ignores.py`
- `gh pr checks <pr-number> --repo kyomind/WeaMind`

If validation cannot be run, report why and what evidence you used instead.

## Report Format

- Checked:
- Action taken:
- Evidence:
- Files changed:
- Verification:
- Remaining items:
- Recommended next step:
