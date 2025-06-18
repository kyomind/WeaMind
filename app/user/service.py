"""用戶服務邏輯."""

from sqlalchemy.orm import Session

from app.user.models import User
from app.user.schemas import UserCreate, UserUpdate


def create_user(db: Session, user_in: UserCreate) -> User:
    """
    建立新用戶

    Args:
        db: 資料庫 Session 物件
        user_in: 用戶註冊資料

    Returns:
        新增後的用戶模型
    """

    user = User(line_user_id=user_in.line_user_id, display_name=user_in.display_name)
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


def get_user(db: Session, user_id: int) -> User | None:
    """依 ID 取得用戶."""

    return db.get(User, user_id)


def update_user(db: Session, user_id: int, user_in: UserUpdate) -> User | None:
    """更新並回傳用戶."""

    user = db.get(User, user_id)
    if user is None:
        return None
    for field, value in user_in.model_dump(exclude_unset=True).items():
        setattr(user, field, value)
    db.commit()
    db.refresh(user)
    return user


def delete_user(db: Session, user_id: int) -> bool:
    """刪除用戶，成功回傳 True."""

    user = db.get(User, user_id)
    if user is None:
        return False
    db.delete(user)
    db.commit()
    return True
