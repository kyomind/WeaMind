from fastapi import APIRouter, HTTPException, status

from app.user import schemas, service


router = APIRouter(prefix="/users")


@router.post("", response_model=schemas.UserRead, status_code=status.HTTP_201_CREATED)
async def create_user(user: schemas.UserCreate) -> schemas.UserRead:

    """
    註冊新用戶

    Returns:
        新建立的用戶資料
    """
    return service.create_user(user)


@router.get("/{user_id}", response_model=schemas.UserRead)
async def get_user(user_id: int) -> schemas.UserRead:
    """
    取得指定用戶
    """
    user = service.get_user(user_id)
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")
    return user


@router.patch("/{user_id}", response_model=schemas.UserRead)
async def update_user(user_id: int, data: schemas.UserUpdate) -> schemas.UserRead:
    """
    更新用戶資料
    """
    user = service.update_user(user_id, data)
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")
    return user



@router.delete("/{user_id}", response_model=dict)
async def delete_user(user_id: int) -> dict[str, bool]:
    """
    刪除指定用戶

    """
    if not service.delete_user(user_id):
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")
    return {"ok": True}


@router.get("", response_model=list[schemas.UserRead])
async def list_users() -> list[schemas.UserRead]:
    """
    列出所有用戶
    """
    return service.list_users()
