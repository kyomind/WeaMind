# AGENT 開發規格：前置準備 (Task 監控表)

本文件提供給 AI Agent 作為 WeaMind 主專案中「前置準備」任務的開發依據。

---

## 1. WHY：為何需要此功能？

- **問題**: `wea-data` 是一個獨立的 ETL 微服務，負責從氣象局抓取資料。我們需要一個機制來監控它每次執行的狀況（成功、失敗、處理筆數等）。
- **目標**: 在 WeaMind 主專案的資料庫中建立一個 `task` 表，專門用來儲存 `wea-data` 服務的執行記錄。這使得監控和偵錯變得簡單，且無需引入複雜的監控系統。

---

## 2. WHAT：需要實作什麼？

1.  **定義 SQLAlchemy Model**: 在 WeaMind 專案中，建立一個名為 `Task` 的 SQLAlchemy model。
2.  **產生資料庫遷移檔**: 使用 Alembic，基於新的 `Task` model 自動產生一個資料庫遷移 (migration) 腳本。
3.  **執行遷移**: 套用該遷移腳本，在 PostgreSQL 資料庫中實際建立 `task` 資料表。

---

## 3. HOW：如何實作？

### 3.1 `Task` Model 定義

- **檔案位置**: 建議在 `app/weather/models.py` 中加入 `Task` 類別，因為它與天氣資料的更新流程密切相關。
- **欄位設計**: 必須嚴格遵循我們在 `MEMO-for-next-conversation.md` 中確定的最終設計，以確保與 `wea-data` 服務的相容性。

```python
# 參考實作，具體程式碼由 AI Agent 完成
from typing import Optional
from datetime import datetime
from sqlalchemy import String, func
from sqlalchemy.orm import Mapped, mapped_column

# ... 在 existing Base ...

class Task(Base):
    __tablename__ = "task"

    id: Mapped[int] = mapped_column(primary_key=True)
    county: Mapped[str] = mapped_column(String(10))
    start_time: Mapped[datetime] = mapped_column(default=func.now())
    end_time: Mapped[Optional[datetime]]
    is_success: Mapped[bool]
    error_message: Mapped[Optional[str]]
    attempt_count: Mapped[int] = mapped_column(default=1)
    records_processed: Mapped[int] = mapped_column(default=0)
```
### ✅ Task 表最終設計(僅供參考，幫助理解欄位意義)
```sql
CREATE TABLE task (
    id SERIAL PRIMARY KEY,
    county VARCHAR(10) NOT NULL,           -- 縣市名稱，如 "屏東縣"
    start_time TIMESTAMP NOT NULL DEFAULT NOW(),  -- 任務開始時間
    end_time TIMESTAMP,                     -- 任務結束時間
    is_success BOOLEAN NOT NULL,           -- 任務成功/失敗
    error_message TEXT,                     -- 失敗時的錯誤訊息
    attempt_count INTEGER DEFAULT 1,       -- 第幾次嘗試
    records_processed INTEGER DEFAULT 0    -- 處理的 weather 記錄數
);
```

### 3.2 Alembic 遷移流程

**重要**: 需要建立**兩個**獨立的 migration 檔案，以確保權限設定正確。

#### Migration 1: 建立 `task` 表結構
1.  **確保 Model 已被 `env.py` 引用**: 確認 Alembic 的 `env.py` 設定能夠偵測到 `app.weather.models` 中的新 `Task` model。
2.  **產生遷移檔**: 執行 `uv run alembic revision --autogenerate -m "Add task table for wea-data monitoring"`。

#### Migration 2: 設定資料庫權限
3.  **產生權限遷移檔**: 執行 `uv run alembic revision -m "Setup task table permissions"`。
4.  **手動編輯權限設定**: 在第二個 migration 中加入以下權限設定：
    ```sql
    -- 賦予 wea_data 完整權限 (ETL 服務需要寫入監控資料)
    GRANT SELECT, INSERT, UPDATE, DELETE ON task TO wea_data;
    GRANT USAGE, SELECT ON SEQUENCE task_id_seq TO wea_data;

    -- 限制 wea_bot 只有讀取權限 (主應用只需要查看監控資料)
    REVOKE INSERT, UPDATE, DELETE ON task FROM wea_bot;
    GRANT SELECT ON task TO wea_bot;
    ```

#### 執行遷移
5.  **執行遷移**: 執行 `uv run alembic upgrade head`。

---

## 4. 權限設計說明

### 4.1 目前資料庫帳號概況
- **`wea_bot` (`POSTGRES_USER`)**: 資料庫主要擁有者，WeaMind 主應用使用
- **`wea_data` (`WEA_DATA_USER`)**: ETL 服務專用帳號，負責資料抓取和更新

### 4.2 權限設計原則
根據**最小權限原則**和**責任分離**設計：

| 表格       | wea_bot 權限     | wea_data 權限                  | 說明                   |
| ---------- | ---------------- | ------------------------------ | ---------------------- |
| `user`     | 完整權限 (owner) | 無權限                         | 用戶管理，僅主應用需要 |
| `location` | 完整權限 (owner) | SELECT, INSERT, UPDATE         | 地點資料，ETL 需要維護 |
| `weather`  | 僅 SELECT        | SELECT, INSERT, UPDATE, DELETE | 天氣資料，ETL 負責維護 |
| `task`     | 僅 SELECT        | SELECT, INSERT, UPDATE, DELETE | 監控資料，ETL 負責記錄 |

### 4.3 `task` 表權限說明
- **`wea_data` 完整權限**: ETL 服務需要記錄任務狀態、更新結果、清理舊記錄
- **`wea_bot` 僅讀取**: 主應用只需要查看監控資料，用於管理介面或偵錯

---

## 5. Memory Hooks for AI Agent

- **核心提醒 (Memento)**:
    - **職責單一**: 這個 `task` 表的唯一目的是「監控」，`wea-data` 服務是唯一的寫入者。WeaMind 主應用目前**只需定義它、建立它**，不需要任何讀取或寫入 `task` 表的業務邏輯。
    - **設計已定**: `Task` model 的欄位設計是最終版本，請勿修改、增加或刪減任何欄位，以免破壞與 `wea-data` 的契約。
    - **前置作業**: 這是 `wea-data` 服務能正確運作的**前置依賴**。沒有這個表，ETL 流程將因無法記錄日誌而失敗。
    - **無關功能**: 此表與 LINE Bot 的天氣查詢功能**完全無關**。
    - **權限設計**: 必須建立兩個 migration - 第一個建立表結構，第二個設定權限。`wea_data` 需要完整權限，`wea_bot` 限制為只讀。

---
**相關文件**:
- `prd/wea_data/MEMO-for-next-conversation.md` (最終決策)
- `prd/wea_data/wea-data-architecture.md` (架構設計)
