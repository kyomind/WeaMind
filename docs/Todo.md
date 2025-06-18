# Todo List for this Project

- [x] 1.Pydantic的FastAPI config設定 2025-05-15
- [x] 2.🧃新增 pyright 作為專案的 type checker 2025-05-16
- [x] 3.db遷移工具設定檔(還沒真的第一次遷移) 2025-05-30
- [x] 4.🍎🍎🍎專案容器化（尤其是開發用 db）2025-06-16
- [x] 5.設定第一個 api 並成功運行 FastAPI app runtime 2025-06-16
- [x] 6.設定與撰寫基本 api 測試(demo) 2025-06-16
- [x] 7.🍎建議部署和開發用的不同版的docker-compose.yml，使用繼承方式 2025-06-16
- [x] 8.🍎設定好 coverage 測試，cli、xml 等報告 2025-06-17
- [x] 9.將todo prompt和arch prompt移至docs目錄下 2025-06-17
- [x] 10.設計 user 模組的 Pydantic schema 與基本 CRUD API 2025-06-18
- [x] 11.🍎重構測試、建立 fixture 與型別註記，並補充註解說明 2025-06-18
- [ ] 12.建立 line webhook API endpoint，能正確接收與驗證來自 LINE 的 webhook 請求
  - **目的**：建立一個可接收 LINE webhook 請求的 API endpoint，並驗證請求的合法性。由於本專案現階段唯一且最重要的 API 即為此 webhook，應直接設置於 `app/main.py`，作為專案的中心 API 入口。
  - **預期成果**：能夠於 FastAPI app 的主程式中正確接收來自 LINE 的 webhook 請求，並驗證簽名，確保安全性。
  - **可能的挑戰**：
    - 需正確解析 LINE 傳來的 JSON 結構。
    - 驗證 X-Line-Signature 標頭，確保請求來自 LINE 官方。
    - 處理 webhook event 的異常情境（如重複、格式錯誤等）。
    - 需考慮未來若有多個 webhook 或 API 時的結構擴充性。
  - **實作方向與細節**：
    1. 於 `app/main.py` 直接建立 `/line/webhook` POST endpoint，作為專案主要 API 入口。
    2. 解析 request body，並驗證 X-Line-Signature。
    3. 驗證方式可參考 LINE 官方文件，需用 channel secret 計算 HMAC-SHA256。
    4. 撰寫單元測試，模擬 webhook 請求與驗證。
    5. 撰寫文件，說明如何設定 channel secret 及測試 webhook。
    6. 若未來 API 增加，可再考慮將 webhook 拆分至專屬模組。
  - **為何重要**：此功能是與 LINE 平台串接的基礎，且現階段為專案唯一且最核心的 API，確保訊息來源安全，並可進行後續 event 處理。
- [ ] 13.執行 Alembic 資料庫遷移，建立 User 表格
  - **目的**：為 `user` 模組建立實際的資料庫表格，使已設計的 User Pydantic schema 和 CRUD API 能夠實際儲存和讀取使用者資料。
  - **預期成果**：在開發資料庫中成功建立 `users` 表格，其結構符合 `app/user/models.py` 中的 `User` 模型定義。User CRUD API 可以透過此表格進行資料的建立、讀取、更新和刪除。
  - **可能的挑戰**：
    - 確保 `alembic.ini` 中的 `sqlalchemy.url` 指向正確的開發資料庫 (例如 Docker 容器中的 PostgreSQL)。
    - `migrations/env.py` 需要正確設定以偵測 `app.user.models.Base` 的元數據。
    - 首次執行遷移可能因環境設定或模型定義問題而出錯。
  - **實作方向與細節**：
    1. 確認 `app/user/models.py` 中的 `User` SQLAlchemy 模型已最終確定。
    2. 在 `migrations/env.py` 中，確保 `target_metadata` 設定為 `app.user.models.Base.metadata` (或專案中所有模型的共同 Base)。
    3. 執行 `alembic revision -m "create_user_table"` 以產生新的遷移腳本。
    4. 檢查並修改產生的遷移腳本，確保它包含了創建 `users` 表格的 `op.create_table()` 指令，以及對應的欄位和約束。
    5. 執行 `alembic upgrade head` 以套用遷移。
    6. 使用資料庫客戶端工具連接到開發資料庫，驗證 `users` 表格已按預期建立。
  - **為何重要**：此任務是銜接使用者模型/API 設計與實際功能的關鍵。沒有資料庫表格，使用者資料無法持久化，先前開發的 CRUD API 也無法真正運作。完成此任務將使專案具備基本的使用者管理能力。

## 說明

- 日期格式為 YYYY-MM-DD，代表「已完成日期」，如果沒有日期則代表還沒完成
- 🍎代表可作為文章素材
- 🧃代表已撰寫文章
