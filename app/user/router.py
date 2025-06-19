from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.user import service
from app.user.schemas import UserCreate, UserRead, UserUpdate

router = APIRouter(prefix="/users")


@router.post("", status_code=status.HTTP_201_CREATED)
async def create_user(
    payload: UserCreate,
    db: Annotated[Session, Depends(get_db)],
) -> UserRead:
    """
    Register a new user
    """
    try:
        user = service.create_user(db, payload)
        return UserRead.model_validate(user)
    except IntegrityError as exc:  # noqa: B904
        raise HTTPException(status_code=400, detail="User already exists") from exc


@router.get("/{user_id}")
async def get_user(
    user_id: int,
    db: Annotated[Session, Depends(get_db)],
) -> UserRead:
    """
    Retrieve a single user
    """
    user = service.get_user(db, user_id)
    if user is None:
        raise HTTPException(status_code=404, detail="User not found")
    return UserRead.model_validate(user)


@router.patch("/{user_id}")
async def update_user(
    user_id: int,
    payload: UserUpdate,
    db: Annotated[Session, Depends(get_db)],
) -> UserRead:
    """
    Update user information
    """
    user = service.update_user(db, user_id, payload)
    if user is None:
        raise HTTPException(status_code=404, detail="User not found")
    return UserRead.model_validate(user)


@router.delete("/{user_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_user(
    user_id: int,
    db: Annotated[Session, Depends(get_db)],
) -> None:
    """
    Delete a user
    """
    if not service.delete_user(db, user_id):
        raise HTTPException(status_code=404, detail="User not found")
