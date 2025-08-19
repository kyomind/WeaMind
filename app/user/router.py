"""User management API routes and endpoints."""

from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.core.auth import get_current_line_user_id_from_access_token
from app.core.database import get_session
from app.user import service
from app.user.schemas import (
    LocationSettingRequest,
    LocationSettingResponse,
)

router = APIRouter(prefix="/users")


@router.post("/locations")
async def set_user_location(
    payload: LocationSettingRequest,
    line_user_id: Annotated[str, Depends(get_current_line_user_id_from_access_token)],
    session: Annotated[Session, Depends(get_session)],
) -> LocationSettingResponse:
    """
    Set user's home or work location via LIFF.

    This endpoint is called from the LIFF location setting page.
    It requires a valid LINE Access Token for authentication.
    """
    # Validate location data against administrative divisions
    success, message, _ = service.set_user_location(
        session=session,
        line_user_id=line_user_id,
        location_type=payload.location_type,
        county=payload.county,
        district=payload.district,
    )

    if not success:
        raise HTTPException(status_code=400, detail=message)

    location_type_text = "住家" if payload.location_type == "home" else "公司"
    full_location = f"{payload.county}{payload.district}"

    return LocationSettingResponse(
        success=True,
        message=f"{location_type_text}地點設定成功",
        location_type=location_type_text,
        location=full_location,
    )
