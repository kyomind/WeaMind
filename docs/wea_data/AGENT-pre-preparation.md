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

1.  **確保 Model 已被 `env.py` 引用**: 確認 Alembic 的 `env.py` 設定能夠偵測到 `app.weather.models` 中的新 `Task` model。
2.  **產生遷移檔**: 執行 `uv run alembic revision --autogenerate -m "Add task table for wea-data monitoring"`。
3.  **執行遷移**: 執行 `uv run alembic upgrade head`。

---

## 4. Memory Hooks for AI Agent

- **核心提醒 (Memento)**:
    - **職責單一**: 這個 `task` 表的唯一目的是「監控」，`wea-data` 服務是唯一的寫入者。WeaMind 主應用目前**只需定義它、建立它**，不需要任何讀取或寫入 `task` 表的業務邏輯。
    - **設計已定**: `Task` model 的欄位設計是最終版本，請勿修改、增加或刪減任何欄位，以免破壞與 `wea-data` 的契約。
    - **前置作業**: 這是 `wea-data` 服務能正確運作的**前置依賴**。沒有這個表，ETL 流程將因無法記錄日誌而失敗。
    - **無關功能**: 此表與 LINE Bot 的天氣查詢功能**完全無關**。

---
**相關文件**:
- `prd/wea_data/MEMO-for-next-conversation.md` (最終決策)
- `prd/wea_data/wea-data-architecture.md` (架構設計)
