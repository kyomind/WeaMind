---
mode: 'agent'
description: 'CLI Output and Tool Usage Best Practices'
---

# CLI Output and Tool Usage Best Practices

## Overview

The `run_in_terminal` tool allows executing shell commands in VS Code environment. Understanding its capabilities and limitations is crucial for effective usage.

## Tool Capabilities & Limitations

### ✅ What Works Well
- **Short commands** with brief output
- **Quick status checks** and simple operations
- **Fast-executing commands** that complete immediately

### ❌ Known Limitations
- **Long output** may be truncated or not displayed
- **Time-consuming operations** may not show completion status
- **Interactive prompts** can cause commands to hang without visible feedback

## Command Classification Guidelines

### Preferred for `run_in_terminal`
- **Simple checks**: `echo`, `ls`, `pwd`, `date`, `whoami`
- **Version queries**: `--version`, `--help` flags
- **Quick file operations**: `touch`, `mv`, `cp` (non-interactive)
- **Status checks**: `git status`, `git branch`, `git log --oneline -5`

### Use Specialized Tools Instead
- **Testing**: Use `runTests` tool rather than `uv run pytest`
- **Coverage analysis**: Read existing `coverage.xml` or `coverage_html_report/index.html`
- **Package installation**: Use with caution due to verbose output
- **Build processes**: Often produce extensive logs that may not display properly

## Specific Command Best Practices

### Interactive Command Handling

When dealing with commands that may prompt for user input:

#### File Deletion
```bash
# Recommended: Force deletion without prompts
rm -f "filename with spaces.txt"
rm -f "file-with-special-chars@#$.md"

#### Batch Operations
```bash
# Multiple file deletion with force flag (recommended)
rm -f file1 file2 file3
```

### File Operations
- **Always quote filenames** with spaces or special characters
- **Use absolute paths** when possible to avoid ambiguity
- **Test commands on non-critical files** first

## Key Operating Principles

1. **Verify before assuming**: Check file timestamps before trusting existing reports
2. **Choose the right tool**: Prefer specialized VS Code tools over terminal for complex operations
3. **Handle interactivity**: Always account for potential user prompts in commands
4. **Acknowledge limitations**: Be transparent when tool limitations may affect results
5. **Start simple**: Use short commands to verify tool behavior before complex operations
