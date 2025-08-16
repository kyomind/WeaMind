"""Pydantic schemas for user data validation and serialization."""

from datetime import datetime

from pydantic import BaseModel


class UserCreate(BaseModel):
    """
    Schema for creating a user.

    Used to validate data during registration
    """

    line_user_id: str
    display_name: str | None = None


class UserRead(BaseModel):
    """
    Schema for reading user data.

    Returned by user-related APIs
    """

    id: int
    line_user_id: str
    display_name: str | None = None
    is_active: bool = True
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class UserUpdate(BaseModel):
    """
    Schema for updating user data.

    Used by the PATCH endpoint
    """

    display_name: str | None = None


class LocationSettingRequest(BaseModel):
    """
    Schema for location setting request from LIFF.

    Used to validate location setting data
    """

    location_type: str  # "home" or "work"
    county: str
    district: str


class LocationSettingResponse(BaseModel):
    """
    Schema for location setting response.

    Returned after successful location setting
    """

    success: bool
    message: str
    location_type: str
    location: str
