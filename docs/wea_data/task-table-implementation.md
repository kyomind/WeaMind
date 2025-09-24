# Task 監控表實作文件

## 概述

本文件記錄了為 WeaMind 專案實作 Task 監控表的完整過程。該表專門用於監控 `wea-data` ETL 服務的執行狀況，包括成功/失敗狀態、處理筆數等關鍵資訊。

**實作日期**: 2025年9月16日
**分支**: `feature/weather-data`
**相關文件**:
- `docs/wea_data/AGENT-pre-preparation.md`
- `.github/prompts/migrations.prompt.md`

## 為何需要此功能？

- **問題**: `wea-data` 是獨立的 ETL 微服務，負責從氣象局抓取資料。需要一個機制來監控每次執行的狀況
- **目標**: 在 WeaMind 主專案的資料庫中建立 `task` 表，專門儲存 `wea-data` 服務的執行記錄
- **效益**: 使監控和偵錯變得簡單，無需引入複雜的監控系統

## 資料表設計

### Task Model 規格

```python
class Task(Base):
    """
    Database model for monitoring wea-data ETL service execution.
    Records task status, success/failure, and processing statistics.
    """
    __tablename__ = "task"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    county: Mapped[str] = mapped_column(String(10), nullable=False)
    start_time: Mapped[datetime] = mapped_column(DateTime, default=func.now(), nullable=False)
    end_time: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    is_success: Mapped[bool] = mapped_column(Boolean, nullable=False)
    error_message: Mapped[str | None] = mapped_column(Text, nullable=True)
    attempt_count: Mapped[int] = mapped_column(Integer, default=1, nullable=False)
    records_processed: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
```

### 欄位說明

| 欄位名稱            | 資料型別    | 說明                  | 預設值 |
| ------------------- | ----------- | --------------------- | ------ |
| `id`                | SERIAL      | 主鍵，自動遞增        | AUTO   |
| `county`            | VARCHAR(10) | 縣市名稱，如 "屏東縣" | -      |
| `start_time`        | TIMESTAMP   | 任務開始時間          | NOW()  |
| `end_time`          | TIMESTAMP   | 任務結束時間          | NULL   |
| `is_success`        | BOOLEAN     | 任務成功/失敗         | -      |
| `error_message`     | TEXT        | 失敗時的錯誤訊息      | NULL   |
| `attempt_count`     | INTEGER     | 第幾次嘗試            | 1      |
| `records_processed` | INTEGER     | 處理的 weather 記錄數 | 0      |

## 實作步驟

### 1. 建立 SQLAlchemy Model

**檔案**: `app/weather/models.py`

```python
# 新增 imports
from sqlalchemy import (
    Boolean,  # 新增
    CheckConstraint,
    DateTime,
    ForeignKey,
    Integer,
    Numeric,
    String,
    Text,
    UniqueConstraint,
    func,  # 新增
)

# 在檔案末尾新增 Task 類別
class Task(Base):
    # ... (如上述 Model 規格)
```

**檔案**: `migrations/env.py`

```python
# 更新 imports 以包含 Task model
from app.weather.models import Location, Weather, Task  # noqa: F401
```

### 2. 產生 Migration 檔案

#### Migration 1: 建立表結構

**命令**:
```bash
make revision
# 或
docker compose exec app uv run alembic revision --autogenerate -m "feature/weather-data_20250916_212057"
```

**產生的檔案**: `1a4a3abc97f6_add_task_table_for_wea_data_monitoring.py`

```python
def upgrade() -> None:
    """Upgrade schema."""
    op.create_table('task',
    sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
    sa.Column('county', sa.String(length=10), nullable=False),
    sa.Column('start_time', sa.DateTime(), nullable=False),
    sa.Column('end_time', sa.DateTime(), nullable=True),
    sa.Column('is_success', sa.Boolean(), nullable=False),
    sa.Column('error_message', sa.Text(), nullable=True),
    sa.Column('attempt_count', sa.Integer(), nullable=False),
    sa.Column('records_processed', sa.Integer(), nullable=False),
    sa.PrimaryKeyConstraint('id')
    )

def downgrade() -> None:
    """Downgrade schema."""
    op.drop_table('task')
```

#### Migration 2: 設定權限

**命令**:
```bash
docker compose exec app uv run alembic revision -m "setup_task_table_permissions"
```

**產生的檔案**: `8ef96c483fc9_setup_task_table_permissions.py`

```python
def upgrade() -> None:
    """Setup task table permissions for wea_data and wea_bot users."""
    # Grant full permissions to wea_data (ETL service needs to write monitoring data)
    op.execute("GRANT SELECT, INSERT, UPDATE, DELETE ON task TO wea_data")
    op.execute("GRANT USAGE, SELECT ON SEQUENCE task_id_seq TO wea_data")

    # Restrict wea_bot to read-only access (main app only needs to view monitoring data)
    op.execute("REVOKE INSERT, UPDATE, DELETE ON task FROM wea_bot")
    op.execute("GRANT SELECT ON task TO wea_bot")

def downgrade() -> None:
    """Revert task table permissions."""
    # Revoke all permissions from both users
    op.execute("REVOKE ALL ON task FROM wea_data")
    op.execute("REVOKE ALL ON SEQUENCE task_id_seq FROM wea_data")
    op.execute("REVOKE ALL ON task FROM wea_bot")
```

### 3. 執行 Migration

**命令**:
```bash
make migrate
# 或
docker compose exec app uv run alembic upgrade head
```

**執行結果**:
```
INFO  [alembic.runtime.migration] Running upgrade cdb5dd844b83 -> 1a4a3abc97f6, feature/weather-data_20250916_212057
INFO  [alembic.runtime.migration] Running upgrade 1a4a3abc97f6 -> 8ef96c483fc9, setup_task_table_permissions
```

## 權限設計

### 權限原則

基於**最小權限原則**和**責任分離**設計：

| 資料表     | wea_bot 權限     | wea_data 權限                  | 說明                   |
| ---------- | ---------------- | ------------------------------ | ---------------------- |
| `user`     | 完整權限 (owner) | 無權限                         | 用戶管理，僅主應用需要 |
| `location` | 完整權限 (owner) | SELECT, INSERT, UPDATE         | 地點資料，ETL 需要維護 |
| `weather`  | 僅 SELECT        | SELECT, INSERT, UPDATE, DELETE | 天氣資料，ETL 負責維護 |
| `task`     | 僅 SELECT        | SELECT, INSERT, UPDATE, DELETE | 監控資料，ETL 負責記錄 |

### Task 表權限詳情

#### wea_data 使用者 (完整權限)
```sql
GRANT SELECT, INSERT, UPDATE, DELETE ON task TO wea_data;
GRANT USAGE, SELECT ON SEQUENCE task_id_seq TO wea_data;
```

**理由**: ETL 服務需要：
- 記錄任務開始 (INSERT)
- 更新執行狀況 (UPDATE)
- 清理舊記錄 (DELETE)
- 查詢歷史記錄 (SELECT)

#### wea_bot 使用者 (只讀權限)
```sql
REVOKE INSERT, UPDATE, DELETE ON task FROM wea_bot;
GRANT SELECT ON task TO wea_bot;
```

**理由**: 主應用只需要：
- 查看監控資料 (SELECT)
- 用於管理介面或偵錯

## 檔案變更清單

### 新增檔案
- `migrations/versions/1a4a3abc97f6_add_task_table_for_wea_data_monitoring.py`
- `migrations/versions/8ef96c483fc9_setup_task_table_permissions.py`

### 修改檔案
- `app/weather/models.py` - 新增 Task 類別和相關 imports
- `migrations/env.py` - 新增 Task model import

## 驗證方式

### 1. 檢查表結構
```sql
\d task
```

### 2. 檢查權限
```sql
-- 檢查 wea_data 權限
SELECT privilege_type FROM information_schema.table_privileges
WHERE table_name = 'task' AND grantee = 'wea_data';

-- 檢查 wea_bot 權限
SELECT privilege_type FROM information_schema.table_privileges
WHERE table_name = 'task' AND grantee = 'wea_bot';
```

### 3. 測試 ETL 服務整合
```python
# wea-data 服務應能成功執行以下操作
from app.weather.models import Task

# 記錄任務開始
task = Task(county="屏東縣", is_success=False)
session.add(task)
session.commit()

# 更新任務結果
task.end_time = datetime.now()
task.is_success = True
task.records_processed = 150
session.commit()
```

## 重要注意事項

### ⚠️ 設計限制
- **欄位固定**: Task model 的欄位設計是最終版本，請勿修改、增加或刪減，以免破壞與 `wea-data` 的契約
- **前置依賴**: 這是 `wea-data` 服務能正確運作的前置依賴，沒有這個表 ETL 流程將失敗
- **職責單一**: 此表的唯一目的是「監控」，`wea-data` 服務是唯一的寫入者

### 🎯 使用範圍
- ✅ **適用於**: ETL 服務監控、偵錯、管理介面展示
- ❌ **不適用於**: LINE Bot 天氣查詢功能（完全無關）
- ❌ **不需要**: WeaMind 主應用目前不需要任何讀取或寫入 `task` 表的業務邏輯

## 後續工作

1. **wea-data 服務整合**: 在 ETL 服務中實作 Task 記錄邏輯
2. **監控介面**: 可考慮在管理介面中展示 Task 執行狀況
3. **清理機制**: 可設定定期清理舊的 Task 記錄，避免資料表過大

## 相關文件

- [前置準備規格](./AGENT-pre-preparation.md)
- [Migration 指引](./../.github/prompts/migrations.prompt.md)
- [專案架構](../Architecture.md)
- [WeaMind Coding Agent Instructions](../.github/copilot-instructions.md)
