---
applyTo: 'tests/**/*.py'
---

# Test Execution Tool Usage Guidelines

## 🎯 Preferred Choice: VS Code Built-in Tools
**Strongly recommended to prioritize** VS Code specialized testing tools:
- `runTests` tool (best choice)
- `test_failure` tool (get failure details)
- `get_errors` tool (check file errors)

## ⚠️ CLI Limitations
Issues when using `run_in_terminal` to execute tests:
- Output may be truncated, unable to see complete results
- AI agents struggle to correctly determine test results
- Cannot integrate with VS Code test explorer

## 📝 Recommended Usage
```python
# Execute specific test file
runTests(files=["/path/to/test_file.py"])

# Execute specific test case
runTests(files=["/path/to/test_file.py"], testNames=["test_function"])

# Check failure details
test_failure()
```

## 🔧 CLI Fallback Option
When VS Code tools are unavailable:
```bash
# Execute specific test with short output
uv run pytest tests/specific_test.py --tb=short
```

## 🛑 Critical Principle: Stop Ineffective Attempts
**If CLI execution shows no results or output, STOP immediately!**

### What NOT to do:
- ❌ Repeat the same CLI command
- ❌ Try other CLI variations

### What TO do:
- ✅ Inform user that output may be truncated
- ✅ Ask user to supplement via built-in tools
- ✅ Request user confirmation to continue

**Remember: Ineffective repeated attempts waste tokens!**

---
**Core Principle: Prioritize VS Code built-in tools, CLI is fallback only.**
