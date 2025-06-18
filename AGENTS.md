# AGENTS.md

## 測試命令

- 運行測試：`uv run pytest`
- 風格檢查：`uv run ruff check .`
- 格式化：`uv run ruff format .`

## Coding Guidelines

- 使用型別提示（Type Hints）確保 FastAPI 路由與模型的型別安全。
- 所有函式需包含 Docstring，遵循 `.github/prompts/docstring.prompt.md` 標準。

## Commit Message Guidelines

Write a concise and natural commit message summarizing the following code diff in English. Avoid listing specific method or variable names unless essential. Focus on the overall intent of the change. Keep the message short and readable, ideally under 10 words. Do not invent motivations unless explicitly obvious in the code.

## WeaMind 高階架構說明

- 三元件分離：line-bot(FastAPI app，即本專案), wea-data(定期更新氣象資料), wea-ai(提供 AI 相關功能)
- wea-ai：獨立部署，只出 intent/schema，不直接存取資料
- wea-data：獨立部署，負責 ETL，從外部資料來源更新最新的氣象資料

## 專案範圍說明

- 本 repo 僅包含 **line-bot** 模組程式碼
- wea-data 與 wea-ai 為獨立元件(微服務)，不在此 repo 中

## 重要參考資料

- 待辦事項清單：`docs/Todo.md`
  - 待辦事項範例：`docs/Example.md`
- 專案架構與技術決策：`docs/Architecture.md`
- 專案目錄結構：`docs/Tree.md`
