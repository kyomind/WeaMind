# Todo Example with Details

- [ ] 12.執行 Alembic 資料庫遷移，建立 User 表格
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
