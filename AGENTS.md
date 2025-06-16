# AGENTS.md (適用於本專案——WeaMind Line Bot)

## 測試命令

- 運行測試：`uv run pytest`(暫無測試)
- 風格檢查：`uv run ruff check .`
- 格式化代碼：`uv run ruff format .`

## 編碼指導方針

- 使用型別提示（Type Hints）確保 FastAPI 路由與模型的型別安全。
- 所有函式需包含 docstrings，遵循 `.github/prompts/docstring.prompt.md` 標準。

## Pull Request 規範

- PR 描述需包含變更概述、測試結果及影響範圍。

## WeaMind 高階架構說明

- 三元件分離：line-bot(FastAPI app，即本專案), wea-data(定期更新氣象資料), wea-ai(提供 AI 相關功能)
- wea-ai：獨立部署，只出 intent/schema，不直接存取資料
- wea-data：獨立部署，負責 ETL，從外部資料來源更新最新的氣象資料

## 專案範圍說明

- 本 repo 僅包含 **line-bot** 模組程式碼
- wea-data 與 wea-ai 為獨立元件(微服務)，不在此 repo 中
