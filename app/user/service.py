"""User service logic."""

from sqlalchemy.orm import Session

from app.user.models import User
from app.user.schemas import UserCreate, UserUpdate


def create_user(session: Session, user_in: UserCreate) -> User:
    """
    Create a new user.

    Args:
        session: database Session object
        user_in: registration data for the user

    Returns:
        The newly created user model
    """

    user = User(line_user_id=user_in.line_user_id, display_name=user_in.display_name)
    session.add(user)
    session.commit()
    session.refresh(user)
    return user


def get_user(session: Session, user_id: int) -> User | None:
    """Get a user by ID."""

    return session.get(User, user_id)


def update_user(session: Session, user_id: int, user_in: UserUpdate) -> User | None:
    """Update and return a user."""

    user = session.get(User, user_id)
    if user is None:
        return None
    for field, value in user_in.model_dump(exclude_unset=True).items():
        setattr(user, field, value)
    session.commit()
    session.refresh(user)
    return user


def delete_user(session: Session, user_id: int) -> bool:
    """Delete a user and return True if successful."""

    user = session.get(User, user_id)
    if user is None:
        return False
    session.delete(user)
    session.commit()
    return True


def get_user_by_line_id(session: Session, line_user_id: str) -> User | None:
    """Get a user by LINE user ID."""
    return session.query(User).filter(User.line_user_id == line_user_id).first()


def create_user_if_not_exists(
    session: Session, line_user_id: str, display_name: str | None = None
) -> User:
    """
    Create a user if not exists, or reactivate if exists but inactive.

    Args:
        session: database Session object
        line_user_id: LINE user ID
        display_name: display name of the user

    Returns:
        The user model (either created or reactivated)
    """
    existing_user = get_user_by_line_id(session, line_user_id)

    if existing_user:
        # Reactivate if the user exists but is inactive
        if not existing_user.is_active:
            existing_user.is_active = True
            if display_name:
                existing_user.display_name = display_name
            session.commit()
            session.refresh(existing_user)
        return existing_user
    else:
        # Create new user
        user = User(line_user_id=line_user_id, display_name=display_name, is_active=True)
        session.add(user)
        session.commit()
        session.refresh(user)
        return user


def deactivate_user(session: Session, line_user_id: str) -> User | None:
    """
    Soft delete (deactivate) a user by LINE user ID.

    Args:
        session: database Session object
        line_user_id: LINE user ID

    Returns:
        The deactivated user model or None if not found
    """
    user = get_user_by_line_id(session, line_user_id)
    if user:
        user.is_active = False
        session.commit()
        session.refresh(user)
        return user
    return None
