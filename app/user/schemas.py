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
    讀取用戶資料模型

    回應用戶相關 API 時使用
    """

    id: int
    line_user_id: str
    display_name: str | None = None
    quota: int = 5
    quota_used: int = 0

    model_config = ConfigDict(from_attributes=True)


class UserUpdate(BaseModel):
    """
    用戶更新資料模型

    提供 PATCH 方法修改用戶資訊
    """

    display_name: str | None = None
