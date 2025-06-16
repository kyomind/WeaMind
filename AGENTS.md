# AGENTS.md

## 測試命令

- 運行測試：`uv run pytest`(暫無測試)
- 風格檢查：`uv run ruff check .`
- 格式化：`uv run ruff format .`

## Coding Guidelines

- 使用型別提示（Type Hints）確保 FastAPI 路由與模型的型別安全。
- 所有函式需包含 Docstring，遵循 `.github/prompts/docstring.prompt.md` 標準。

## Commit Message Guidelines

Write a concise and natural commit message summarizing the following code diff in English. Avoid listing specific method or variable names unless essential. Focus on the overall intent of the change. Keep the message short and readable, ideally under 10 words. Do not invent motivations unless explicitly obvious in the code.

## Branch Naming Guidelines

- 語言：英語（English）
- 格式：小寫+kebab-case（使用連字號 `-` 分隔單字）
- 示例：
  - 功能分支：`feature/add-weather-api`
  - 修復分支：`fix/bug-handle-empty-response`
  - 重構分支：`refactor/cleanup-line-handlers`
  - 文檔更新：`docs/update-agents-guidelines`
- 原則：描述要簡潔明確，最多三到五個單字。

## WeaMind 高階架構說明

- 三元件分離：line-bot(FastAPI app，即本專案), wea-data(定期更新氣象資料), wea-ai(提供 AI 相關功能)
- wea-ai：獨立部署，只出 intent/schema，不直接存取資料
- wea-data：獨立部署，負責 ETL，從外部資料來源更新最新的氣象資料

## 專案範圍說明

- 本 repo 僅包含 **line-bot** 模組程式碼
- wea-data 與 wea-ai 為獨立元件(微服務)，不在此 repo 中

## Todo List for this Project(important)

目前已完成及待辦事項放在`.github/prompts/todo.prompt.md`。
