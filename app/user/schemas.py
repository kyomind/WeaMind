"""Pydantic schemas for user data validation and serialization."""

from pydantic import BaseModel


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
