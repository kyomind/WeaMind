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
    user_in: UserCreate,
    db: Annotated[Session, Depends(get_db)],
) -> UserRead:
    """
    註冊新用戶

    Args:
        user_in: 用戶註冊資料
        db: 資料庫 Session 物件

    Returns:
        建立完成的用戶資料
    """

    try:
        user = service.create_user(db, user_in)
        return UserRead.model_validate(user)
    except IntegrityError as exc:  # noqa: B904
        raise HTTPException(status_code=400, detail="User already exists") from exc


@router.get("/{user_id}")
async def get_user(
    user_id: int,
    db: Annotated[Session, Depends(get_db)],
) -> UserRead:
    """
    取得單一用戶資料

    Args:
        user_id: 用戶 ID
        db: 資料庫 Session 物件

    Returns:
        用戶詳細資料
    """

    user = service.get_user(db, user_id)
    if user is None:
        raise HTTPException(status_code=404, detail="User not found")
    return UserRead.model_validate(user)


@router.patch("/{user_id}")
async def update_user(
    user_id: int,
    user_in: UserUpdate,
    db: Annotated[Session, Depends(get_db)],
) -> UserRead:
    """
    更新用戶資料

    Args:
        user_id: 用戶 ID
        user_in: 欲更新的資料
        db: 資料庫 Session 物件

    Returns:
        更新後的用戶資料
    """

    user = service.update_user(db, user_id, user_in)
    if user is None:
        raise HTTPException(status_code=404, detail="User not found")
    return UserRead.model_validate(user)


@router.delete("/{user_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_user(
    user_id: int,
    db: Annotated[Session, Depends(get_db)],
) -> None:
    """
    刪除用戶

    Args:
        user_id: 用戶 ID
        db: 資料庫 Session 物件
    """

    if not service.delete_user(db, user_id):
        raise HTTPException(status_code=404, detail="User not found")
