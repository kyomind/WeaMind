---
description: "檢查提供的拼字警告，將合法專有名詞加入 cSpell 字典"
---

# Update the Spelling Dictionary

## Goal

Resolve the supplied cSpell warnings by distinguishing legitimate terms from spelling mistakes. Update `cSpell.words` in `.vscode/settings.json` only for valid terms.

## Workflow

1. Read the supplied warnings or explicit word list. Accept editor diagnostics, pasted text, or `<error>` attachments; do not require a particular editor or attachment format. If no words or diagnostics are supplied, ask for them and stop rather than scanning unrelated files.
2. Inspect the terms in context. Add legitimate project names, technical terms, and proper nouns. Correct obvious spelling mistakes at their source instead of whitelisting them; ask when the intended spelling is uncertain.
3. Read `.vscode/settings.json`. Merge approved terms into `cSpell.words`, deduplicate, and sort alphabetically. Preserve unrelated settings, comments, and formatting. Do not add a new dictionary dependency.
4. Check the diff for unintended changes and validate the settings format. Rerun the relevant spelling check if available; otherwise report that editor diagnostics have not been rechecked.

## Output

Report terms added, source typos corrected, uncertain terms left unchanged, and validation performed. Do not claim all warnings are resolved without rerunning the check.
