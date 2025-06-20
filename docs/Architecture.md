# WeaMind System Documentation

## WeaMind 高階架構說明

- 三元件分離：line-bot(FastAPI app，即本專案), wea-data(定期更新氣象資料), wea-ai(提供 AI 相關功能)
- wea-ai：獨立部署，只出 intent/schema，不直接存取資料
- wea-data：獨立部署，獨立運作，不和上述二者互動。僅負責 ETL，從外部資料來源更新最新的氣象資料

## 專案範圍說明

- 本 repo 僅包含 **line-bot** 模組程式碼
- wea-data 與 wea-ai 為獨立元件(微服務)，不在此 repo 中

## 元件互動流程

- line-bot 透過 HTTP API 與 wea-ai 溝通，所有外部請求皆由 line-bot 統一進出。
- line-bot 處理 LINE webhook 事件，根據 intent 轉發至 wea-ai。
- wea-data 僅負責定期 ETL，將氣象資料寫入資料庫，不對外提供 API。
- 所有資料查詢與存取皆由 line-bot 直接操作資料庫。
- wea-ai 提供意圖判斷與對話 schema，不直接存取資料。

## 主要模組職責

- app/core：全域設定、資料庫連線
- app/user：使用者資料模型、CRUD API、驗證
- app/main.py：FastAPI app 啟動點，註冊路由

## 資料流向與持久化

- wea-data 定期將外部氣象資料 ETL 寫入 PostgreSQL
- line-bot 直接查詢/寫入 PostgreSQL，包含 user 狀態與氣象資料
- Alembic 負責資料庫 schema 遷移
- SQLAlchemy 管理所有資料表

## API 設計原則

- 採 RESTful 風格，JSON 為主要 payload 格式
- 所有 POST/PUT 請求 body 參數統一命名為 payload
- 需驗證來自 LINE 的 webhook 請求簽章

## 技術選型重點

- FastAPI：高效、型別安全、易於測試
- Pydantic：資料驗證與序列化
- SQLAlchemy 2.0：ORM，方便管理資料庫
- Alembic：資料庫遷移
- pytest：測試

## 典型請求流程（line webhook 範例）

1. LINE 平台推送 webhook 至 /line/webhook
2. line-bot 驗證簽章，解析事件
3. 根據事件內容，查詢 user 狀態或呼叫 wea-ai 判斷 intent
4. 若需氣象資料：
   - 固定格式查詢：line-bot 直接查詢資料庫
   - 自然語言查詢：line-bot 先與 wea-ai 互動取得 intent，再查詢資料庫，反覆直到獲得明確結果
5. 組合回應訊息，回傳給 LINE 平台
