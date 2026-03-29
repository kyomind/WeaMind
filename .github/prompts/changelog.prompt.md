---
description: "CHANGELOG maintenance and release workflow"
---

# WeaMind CHANGELOG Maintenance Guide

## Purpose

Use this prompt when the user asks to update the CHANGELOG or release a version. Prefer the Makefile and existing scripts. Keep the release workflow consistent and do not skip steps.

## Rules

1. Use the Makefile commands first.
2. Follow the standard release flow in order.
3. Keep the CHANGELOG user-facing, concise, and focused on product value.
4. Exclude non-functional changes such as spelling rules, documentation cleanup, dependency bumps, CI changes, refactors, and formatting-only edits.
5. For major or minor releases, write a fuller entry. For patch releases, keep the entry short.

## Release Flow

1. Check the current status with `make changelog-status`.
   - Confirm the current version and branch.
   - Count commits since the last release.
   - Review the summary of changes.
2. Prepare the release input with `make changelog-prepare VERSION=x.y.z`.
   - Collect commit data.
   - Generate the Copilot Chat prompt text.
   - Produce a formatted change list.
3. Write the CHANGELOG entry in Copilot Chat using the prepared commits.
   - Use Keep a Changelog format.
   - Write in Traditional Chinese.
   - Focus on user value and product impact.
   - Add only meaningful product changes.
4. Release the version with `make changelog-release VERSION=x.y.z`.
   - Update the version in `pyproject.toml`.
   - Run `uv lock` to refresh `uv.lock`.
   - Commit `CHANGELOG.md`, `pyproject.toml`, and `uv.lock`.
   - Create the git tag.
   - Push the changes.
   - Trigger GitHub Actions to create the release.

## CHANGELOG Writing Rules

### Format

Use this heading format:

## [version] - YYYY-MM-DD

### Section Order

1. Added
2. Fixed
3. Changed

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
- dependency version bumps
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

- `git log --oneline v0.1.0..HEAD`
- `git log --oneline --merges v0.1.0..HEAD`
- `git diff --stat v0.1.0..HEAD`

## Checklist

- Run `make changelog-status`.
- Run `make changelog-prepare VERSION=x.y.z`.
- Draft the CHANGELOG entry from the prepared commits.
- Run `make changelog-release VERSION=x.y.z`.
- Confirm the GitHub Actions release succeeded.

## Output Requirements

When finishing, report:

1. the version being released
2. the source commits used
3. the files updated
4. the verification result
