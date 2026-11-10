# Domain Docs

## Before exploring

- Read root `GLOSSARY.md`.
- Read ADRs in `docs/adr/` relevant to the area being explored.

If these files do not exist, proceed silently. Do not flag their absence
or suggest creating them upfront. `/domain-modeling`, also reached via
`/grill-with-docs` and `/improve-codebase-architecture`, creates them
lazily when terms or decisions are resolved.

## File structure

This is a single-context repo:

- `GLOSSARY.md`: shared domain vocabulary.
- `docs/adr/`: architecture decision records.

## Use the glossary's vocabulary

Use the glossary's terms in issue titles, proposals, hypotheses, and
test names. Avoid synonyms the glossary explicitly excludes.

If a required concept is missing, reconsider invented terminology
or note the real gap for `/domain-modeling`.

## Flag ADR conflicts

Explicitly identify any proposal that contradicts an existing ADR,
including why the decision may be worth reopening.
