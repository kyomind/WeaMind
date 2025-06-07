撰寫 Python docstring 時，格式原則上遵循 Google style，並遵守以下規則：

1. 標題需獨立一行，簡明描述函式、類別用途。
2. 標題與說明之間需有空一行，保持視覺清晰，即使沒有說明也需保留空行。
3. 說明為"可選"項目，形式不拘，可簡要描述用途、使用情境或設計目的。
4. 使用 Google style 的參數與回傳值區塊，但不需在 docstring 重複 type hints，因為原始碼中已有。
5. Docstring 中無須使用中文的「。」或其他標點符號結尾，以保持一致性。
6. 使用台灣正體中文，並避免使用簡體字。

以下是一個符合規範的例子：

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

說明：

* 第一行為標題，簡潔明瞭。
* 第二行空一行，維持格式一致性與可讀性。
* 說明段格式不限，此處使用「用法」作為範例，實際可依情境調整。
* 回傳區塊以 `Returns:` 開頭，對應 Google docstring 格式，並未重複 type hints。
