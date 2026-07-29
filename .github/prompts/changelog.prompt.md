---
description: "Approval-gated CHANGELOG maintenance and release workflow"
---

# WeaMind CHANGELOG Maintenance Guide

## Purpose

Use this prompt when the user asks to update the CHANGELOG or release a version. Prefer the Makefile and existing scripts. Keep the release workflow consistent and do not skip steps.

## Rules

1. Use the Makefile commands first.
2. Follow the standard release flow in order.
3. Draft the CHANGELOG entry without editing any files, then wait for explicit user approval.
4. Do not update files, commit, tag, push, or release until the user approves the exact CHANGELOG content.
5. Keep the CHANGELOG user-facing, concise, and focused on product value.
6. Exclude non-functional changes such as spelling rules, documentation cleanup, routine dependency bumps, CI changes, refactors, and formatting-only edits.
7. For major or minor releases, write a fuller entry. For patch releases, keep the entry short.

## Required Approval Gate

After preparing the commit data:

1. Draft the complete CHANGELOG entry, including version, date, sections, and bullets.
2. Show the exact proposed Markdown to the user.
3. Report which source commits were included and which meaningful candidates were excluded.
4. Stop and wait for explicit approval such as `核可` or `approved`.

Before approval, do not:

- edit `CHANGELOG.md`
- edit `pyproject.toml` or `uv.lock`
- run `make changelog-release`
- create commits or tags
- push changes or trigger a release

Silence, a version request, or an ambiguous response is not approval. If the user requests revisions, update the draft, show the full revised Markdown, and wait for approval again.

## Release Flow

1. Check the current status with `make changelog-status`.
   - Confirm the current version and branch.
   - Count commits since the last release.
   - Review the summary of changes.
2. Prepare the release input with `make changelog-prepare VERSION=x.y.z`.
   - Collect commit data.
   - Review the generated writing guidance.
   - Identify the product-facing changes since the latest tag.
3. Draft the CHANGELOG entry using the prepared commits.
   - Use Keep a Changelog format.
   - Write in Traditional Chinese.
   - Focus on user value and product impact.
   - Add only meaningful product changes.
   - Do not edit any files yet.
4. Present the exact draft and source-commit summary to the user, then stop.
5. After explicit user approval, write the approved entry to `CHANGELOG.md` without changing its wording.
6. Release the version with `make changelog-release VERSION=x.y.z`.
   - Require a clean `main` branch except for the approved `CHANGELOG.md` change.
   - Update the version in `pyproject.toml`.
   - Run `uv lock` to refresh `uv.lock`.
   - Commit `CHANGELOG.md` separately.
   - Commit `pyproject.toml` and `uv.lock` as the version release.
   - Create and push the annotated version tag.
7. Verify the automated release results.
   - Confirm the main CI and CodeQL runs succeed.
   - Confirm GitHub Release creation succeeds.
   - Confirm the versioned multi-platform GHCR image is published.
   - Confirm the automated `weamind-infra` version-update PR is created.

## CHANGELOG Writing Rules

### Format

Use this heading format:

## [version] - YYYY-MM-DD

### Section Order

Include only sections that contain meaningful entries, in this order:

1. 新增
2. 修正
3. 改進

### Writing Style

- Use language that a general user can understand.
- Explain the user benefit, not just the implementation.
- Keep each bullet to one line when possible.
- Use bold text for the most important items.
- For major or minor releases, include richer detail.
- For patch releases, keep only one or two key items.

### Commit Filtering

Include commits that are clearly user-facing, such as:

- new features
- bug fixes
- user experience improvements
- security updates

Exclude commits that are not user-facing, such as:

- cSpell dictionary updates
- documentation micro-edits
- routine dependency version bumps without a user-facing or security impact
- CI changes
- refactors
- formatting-only changes

## Reference Commands

### Script Commands

- `./scripts/changelog.sh status`
- `./scripts/changelog.sh prepare [ver]`
- `./scripts/changelog.sh release <ver>`
- `./scripts/changelog.sh help`

### Git Reference Commands

- `git log --oneline <latest-tag>..HEAD`
- `git log --oneline --merges <latest-tag>..HEAD`
- `git diff --stat <latest-tag>..HEAD`

## Checklist

- Run `make changelog-status`.
- Run `make changelog-prepare VERSION=x.y.z`.
- Draft the CHANGELOG entry from the prepared commits.
- Show the exact draft and source commits to the user.
- Receive explicit user approval.
- Update `CHANGELOG.md` with the approved content.
- Run `make changelog-release VERSION=x.y.z`.
- Confirm CI, CodeQL, GitHub Release, GHCR publishing, and infra PR creation succeeded.

## Output Requirements

When finishing, report:

1. the version being released
2. the source commits used
3. the files updated
4. the release commits and tag
5. the GitHub Release and infra PR links
6. the verification result
