When writing Python docstrings, follow the Google style as the general principle, and adhere to the following rules:

## Rules

1. The summary should be on a separate line, concisely describing the purpose of the function or class.
2. There must be a blank line between the summary and the description for visual clarity, even if there is no description, the blank line should still be kept.
3. The description is optional and can briefly explain the usage, context, or design intent in any format.
4. Use Google style sections for parameters and return values, but do not repeat type hints in the docstring since they are already present in the source code.
5. Do not end the docstring with a Chinese period or other punctuation, to maintain consistency.
6. Use Traditional Chinese (Taiwan), and avoid using Simplified Chinese characters.

## Component-Specific Guidelines

1. For Router (API) functions and test functions, only a summary docstring is required.
2. For database-related functions, include a description of the connection or session handling if applicable.
3. For utility functions, provide examples of usage if the function is complex or non-intuitive.

## Examples

Here is an example that follows the specification:

```python
def get_db() -> typing.Generator[Session, None, None]:
    """
    建立資料庫連線 Session

    用法：在路由中加上 Depends(get_db)

    Returns:
        資料庫 Session 物件，可用於操作資料庫
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
```

Here is an example for a summary-only docstring (should be three lines):

```python
def ping() -> str:
    """
    服務狀態檢查
    """
    return "pong"
```
