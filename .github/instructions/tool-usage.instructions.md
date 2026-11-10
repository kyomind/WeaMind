---
description: 'Tool usage and command execution guidelines across coding agents'
applyTo: '**'
---

# Tool Usage Guidelines

- Use the tools available in the current agent runtime; do not assume VS Code-specific tools exist.
- Prefer dedicated file-reading and editing tools when available. Use `rg` for text searches and `gh` for GitHub operations.
- Run Python commands with `uv run`. Follow `AGENTS.md` for project checks.
- Keep command output focused. If output is truncated, retrieve the saved output or narrow the query before drawing conclusions.
- Allow sufficient time for long-running commands and confirm their final exit status; partial output is not success.
- Avoid interactive commands in unattended runs. Do not bypass confirmation or add force flags merely to prevent a prompt.
- Before destructive operations, verify the exact target, authorization, and recovery path. Quote shell arguments containing paths or user input.
- Treat existing test and coverage reports as historical evidence until their freshness is established.
- Never print credentials or include them in committed files. Report checks that could not run and why.
