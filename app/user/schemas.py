from pydantic import BaseModel, ConfigDict


class UserCreate(BaseModel):
    """
    用戶創建資料模型

    用於處理新用戶註冊時的資料驗證
    """

    line_user_id: str
    display_name: str | None = None


class UserRead(BaseModel):
    """
    用戶完整資料模型

    包含用戶的所有屬性，包括唯一識別碼和額度資訊
    """

    id: int
    line_user_id: str
    display_name: str | None = None
    quota: int = 5  # 預設每日查詢額度
    quota_used: int = 0

    model_config = ConfigDict(from_attributes=True)


class UserUpdate(BaseModel):
    """
    用戶更新資料模型

    目前僅允許修改顯示名稱
    """

    display_name: str | None = None

    model_config = ConfigDict(from_attributes=True)
