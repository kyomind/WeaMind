---
mode: 'agent'
description: 'Automatically collect all cSpell errors and batch add to dictionary'
---

# Automated Batch Processing of cSpell Errors

Automatically collect cSpell spelling check errors from VS Code and add all unknown words to the dictionary in `.vscode/settings.json` in a single operation.

## Prerequisites

**IMPORTANT**: This prompt requires the user to provide cSpell errors through VS Code's error attachment system using `<error>` tags.

If no `<error>` tags are found in the request, **refuse execution** and instruct the user to:
1. Open VS Code Problems panel
2. Look for cSpell errors (marked as "Unknown word")
3. Select and attach the errors when invoking this prompt

## Execution Workflow

When cSpell errors are provided via `<error>` tags, execute the following steps:

### 1. Parse Error Information
Extract unknown words from `<error>` tags with format:
```xml
<error path="filepath" line="number" code="undefined" severity="info">
"word": Unknown word.
</error>
```

### 2. Read Existing Configuration
Read the existing `cSpell.words` array from `.vscode/settings.json`.

### 3. Merge and Update Dictionary
- Extract unknown words from error messages
- Merge with existing dictionary
- Remove duplicates and sort alphabetically
- Update the `settings.json` file

## Error Attachment Format

VS Code provides cSpell errors in this format:
```xml
<error path="/path/to/file.md" line="50" code="undefined" severity="info">
"Substack": Unknown word.
</error>
```

The unknown word is enclosed in quotes at the beginning of the error message.

## Important Notes

- **Validation Required**: Always check for `<error>` tags before proceeding
- Maintain JSON format integrity in `settings.json`
- Preserve alphabetical ordering of words
- Avoid adding obvious spelling errors (validate word legitimacy)
- Preserve existing `settings.json` formatting style
- Handle multiple occurrences of the same word correctly

## Expected Results

Upon completion, all provided cSpell errors should be resolved, as all unknown words will have been added to the exception dictionary in `.vscode/settings.json`.
