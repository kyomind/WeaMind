"""User service logic."""

from sqlalchemy.orm import Session

from app.user.models import User
from app.user.schemas import UserCreate, UserUpdate


def create_user(db: Session, user_in: UserCreate) -> User:
    """
    Create a new user.

    Args:
        db: database Session object
        user_in: registration data for the user

    Returns:
        The newly created user model
    """

    user = User(line_user_id=user_in.line_user_id, display_name=user_in.display_name)
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


def get_user(db: Session, user_id: int) -> User | None:
    """Get a user by ID."""

    return db.get(User, user_id)


def update_user(db: Session, user_id: int, user_in: UserUpdate) -> User | None:
    """Update and return a user."""

    user = db.get(User, user_id)
    if user is None:
        return None
    for field, value in user_in.model_dump(exclude_unset=True).items():
        setattr(user, field, value)
    db.commit()
    db.refresh(user)
    return user


def delete_user(db: Session, user_id: int) -> bool:
    """Delete a user and return True if successful."""

    user = db.get(User, user_id)
    if user is None:
        return False
    db.delete(user)
    db.commit()
    return True
