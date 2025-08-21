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

## Quick Reference

### Core Principles
- Mirror `app/` directory structure in `tests/`
- Fixtures: verb prefix for helpers, noun for objects
- Variables: use descriptive names, avoid generic terms
- Assertions: status code first, then content validation
- Add `# noqa: S101` for assert statements

### Priority Coverage Areas
1. **Service Layer**: Core business logic
2. **API Endpoints**: All HTTP interfaces
3. **Model Validation**: Data validation logic
4. **Error Handling**: Exception scenarios

## Coverage Analysis Best Practices
- **IMPORTANT**: Always run tests with coverage first to generate fresh reports before analysis
- Use `uv run pytest --cov=app --cov-report=xml --cov-report=html` to generate current reports
- Then read coverage reports: `coverage.xml` or `coverage_html_report/index.html`
- Read HTML report files for detailed coverage information

---

**Note**: These guidelines follow pytest best practices and WeaMind project coding standards.
