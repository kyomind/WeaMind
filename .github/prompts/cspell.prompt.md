---
mode: 'agent'
description: 'Automatically collect all cSpell errors and batch add to dictionary'
---

# Automated Batch Processing of cSpell Errors

Automatically detect all cSpell spelling check errors in the workspace and add all unknown words to the dictionary in `.vscode/settings.json` in a single operation.

## Execution Workflow

When requested by the user, execute the following steps in sequence:

### 1. Scan for Spelling Errors
Use cSpell CLI to scan files and extract unknown words:
- Execute `npx cspell "**/*.md" --no-progress` command
- Parse output format: `filename:line:column - Unknown word (word)`
- Extract all unknown words from parentheses and remove duplicates

### 2. Read Existing Configuration
Read the existing `cSpell.words` array from `.vscode/settings.json`.

### 3. Merge and Update Dictionary
- Merge newly discovered words with existing dictionary
- Remove duplicates and sort alphabetically
- Update the `settings.json` file

## Technical Implementation Details

### cSpell CLI Usage
**Command**: `npx cspell "**/*.md" --no-progress`

**Output Format Example**:
```
ep-01.md:1:15 - Unknown word (Portaly)
ep-06.md:77:4 - Unknown word (devv)
ep-07.md:34:47 - Unknown word (felo)
```

**Advantages**: Accurate, detailed, automatable parsing
**Limitations**: First-time use requires package installation and manual confirmation

### File Scope Configuration
- Default scan: `**/*.md` (suitable for this project)
- Can adjust file patterns based on workspace content
- Supports multiple file type combinations

## Important Notes

- First-time use requires installing the cSpell package
- Maintain JSON format integrity
- Preserve alphabetical ordering
- Avoid adding obvious spelling errors
- Preserve existing `settings.json` formatting style

## Fallback Options

If cSpell CLI is unavailable:
1. Request user to provide VS Code Problems panel screenshot
2. Use `semantic_search` to analyze file content and manually identify potential spelling errors

## Expected Results

Upon completion, all cSpell errors in the workspace should be resolved, as all unknown words will have been added to the exception dictionary.
