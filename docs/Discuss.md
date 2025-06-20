# LINE Bot User Table 討論重點整理

## 1. Table 命名

- 建議使用單數：user

## 2. 欄位設計建議

- id：主鍵，自動遞增
- line_user_id：LINE 平台唯一 ID，唯一且必填
- display_name：LINE 顯示名稱，可選
- is_active：是否有效（布林值，預設 True，可用於記錄封鎖/黑名單）
- created_at：建立時間（時間戳）
- updated_at：更新時間（時間戳）

> 可選欄位：picture_url（快取 LINE 頭像網址）、channel_id（多 channel 支援）、deleted_at（軟刪除）

## 3. 欄位型別與約束建議

- id: Integer, primary_key=True, autoincrement=True
- line_user_id: String, unique=True, nullable=False, index=True
- display_name: String, nullable=True
- is_active: Boolean, default=True, nullable=False
- created_at/updated_at: DateTime, default=func.now(), onupdate=func.now()

## 4. is_active 欄位說明

- 用於記錄 LINE 封鎖 bot（unfollow event）或平台主動封鎖（黑名單）
- 推播時僅對 is_active=True 的 user 執行

## 5. 其他補充

- status_message 欄位通常不需儲存
- picture_url 僅快取用，不需自備 S3
- 若未來有多 channel 或軟刪除需求可預留欄位

## 6. 範例 SQLAlchemy User 類別

```python
from sqlalchemy import Column, Integer, String, Boolean, DateTime, func
from app.db import Base

class User(Base):
    __tablename__ = "user"

    id = Column(Integer, primary_key=True, autoincrement=True)
    line_user_id = Column(String, unique=True, nullable=False, index=True)
    display_name = Column(String, nullable=True)
    is_active = Column(Boolean, default=True, nullable=False)
    created_at = Column(DateTime, default=func.now(), nullable=False)
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now(), nullable=False)
```

## 7. Alembic 遷移注意事項

- target_metadata 設定為 app.user.models.Base.metadata
- 遷移腳本需包含所有必要欄位與約束
- 建表後請用資料庫工具驗證結構

---

如需進階設計（如索引、軟刪除、多 channel 支援），可依需求擴充。
