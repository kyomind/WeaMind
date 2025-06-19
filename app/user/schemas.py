from pydantic import BaseModel


class UserCreate(BaseModel):
    """
    Schema for creating a user

    Used to validate data during registration
    """

    line_user_id: str
    display_name: str | None = None


class UserRead(BaseModel):
    """
    Schema for reading user data

    Returned by user-related APIs
    """

    id: int
    line_user_id: str
    display_name: str | None = None
    quota: int = 5
    quota_used: int = 0

    model_config = {"from_attributes": True}


class UserUpdate(BaseModel):
    """
    Schema for updating user data

    Used by the PATCH endpoint
    """

    display_name: str | None = None
