---
description: "根據專案現況與 GitHub Issues，建議下一個最值得執行的任務"
---

# Suggest the Next Task

## Goal

Recommend one concrete next task based on the user's current goals, the codebase, and existing GitHub Issues. Suggest first; do not create issues or edit backlog files without approval.

## Workflow

1. Read `AGENTS.md`, `docs/agents/issue-tracker.md`, and the architecture or code relevant to the user's goal.
2. Use `gh` to inspect open issues and relevant completed issues in `kyomind/WeaMind`. Treat `docs/Todo.md` as historical context, not the authoritative backlog.
3. Identify one high-value task that is not already completed or duplicated. Prefer an existing actionable issue over inventing a new task. If priorities are unclear, ask the user rather than guessing.
4. Present the recommendation with its purpose, expected outcome, implementation direction, risks, and testable completion criteria. Aim for 45–75 minutes; if the useful task is larger, propose a coherent first slice.
5. Wait for approval. If asked to publish the recommendation, follow the issue-tracker guide to create or update the appropriate issue. Do not append to or reorder `docs/Todo.md`.

## Output

- Recommended task and existing issue link, if any
- Why it should come next
- Scope and completion criteria
- Expected effort and blockers

If no useful task is supported by the evidence, say so. Do not generate work just to fill a backlog.
