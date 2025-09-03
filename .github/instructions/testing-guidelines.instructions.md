---
applyTo: 'tests/**/*.py'
---

# WeaMind Testing Guidelines Index

This file serves as an index for WeaMind testing guidelines. The guidelines have been split into specialized instruction files for better organization and targeted application.

## Instruction Files

### 🔧 testing-fixtures.instructions.md
- **Path**: `.github/instructions/testing-fixtures.instructions.md`
- **Apply to**: `tests/**/conftest.py`
- **Content**: Pytest fixtures naming conventions, organization, and performance considerations
- **Use cases**: When creating or modifying fixture files

### 🧪 testing-functions.instructions.md
- **Path**: `.github/instructions/testing-functions.instructions.md`
- **Apply to**: `tests/**/test_*.py`
- **Content**: Test function structure, naming patterns, assertions, mocking, and parameterized testing
- **Use cases**: When writing or modifying test functions

### 🏃 testing-execution.instructions.md
- **Path**: `.github/instructions/testing-execution.instructions.md`
- **Apply to**: `tests/**/*.py`
- **Content**: Test execution tool usage guidelines, prioritize VS Code built-in tools over CLI
- **Use cases**: When executing or debugging tests

## File Location Guide
If you need to locate these instruction files:
- Use `file_search` tool with pattern: `.github/instructions/testing-*.instructions.md`
- Use `semantic_search` tool with query: "testing guidelines instructions"

## Core Testing Principles
- Mirror `app/` directory structure in `tests/`
- Fixtures: verb prefix for helpers, noun for objects
- Variables: use descriptive names, avoid generic terms
- Assertions: status code first, then content validation
- Add `# noqa: S101` for assert statements

## Priority Coverage Areas
1. **Service Layer**: Core business logic
2. **API Endpoints**: All HTTP interfaces
3. **Model Validation**: Data validation logic
4. **Error Handling**: Exception scenarios

## Coverage Analysis Guidelines
**Preferred approach** (follows CLI best practices):
1. **Check existing reports first**: Read `coverage.xml` or `coverage_html_report/index.html`
2. **Verify report freshness**: Check file timestamps before trusting existing reports
3. **If reports are missing/outdated**: Consider asking user to generate fresh reports
4. **For non-VS Code environments**: Use CLI with caution: `uv run pytest --cov=app --cov-report=html --tb=short`

**Note**: CLI coverage generation may produce verbose output that could be truncated.

---

*Note: These guidelines follow pytest best practices and WeaMind project coding standards.*
