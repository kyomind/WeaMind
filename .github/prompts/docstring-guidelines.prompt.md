---
mode: 'agent'
description: 'Python docstring style guide for function documentation'
---

# Python Docstring Style Guide

When writing Python docstrings, follow the Google style as the general principle, and adhere to the following rules:

## Rules

1. The summary should be on the second line(Ruff D213), concisely describing the purpose of the function or class.
2. Use Google style for parameters and return values. Do not repeat type hints in the docstring.
3. The description is optional and can briefly explain the usage, context, or design intent in any format.
4. There must be a blank line between the summary and the description (if present) for visual clarity.

## Component-Specific Guidelines

1. For Router (API) functions and test functions, only a summary docstring is required.
2. For database-related functions, include a description of the connection or session handling if applicable.
3. For utility functions, provide examples of usage if the function is complex or non-intuitive.
4. For module-level docstrings, include a brief overview of the module's purpose and functionality.

## Examples

Here are examples that follow the specification:

```python
def get_session() -> typing.Generator[Session, None, None]:
    """
    Create a database session.

    Usage: Add Depends(get_session) in your route.

    Returns:
        Database session object for database operations.
    """
    session = SessionLocal()
    try:
        yield session
    finally:
        session.close()
```

One line or three lines are enough for simple functions:
```python
def ping() -> str:
    """Service health check."""
    return "pong"
```
```python
def test_ping() -> None:
    """
    Test service health check.
    """
    assert ping() == "pong"
```
