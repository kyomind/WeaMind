"""User service logic."""

from sqlalchemy.orm import Session

from app.user.models import User
from app.weather.models import Location


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


def get_location_by_county_district(
    session: Session, county: str, district: str
) -> Location | None:
    """
    Get location by county and district.

    Args:
        session: database Session object
        county: county name (e.g., "新北市")
        district: district name (e.g., "永和區")

    Returns:
        The Location model or None if not found
    """
    return (
        session.query(Location)
        .filter(Location.county == county, Location.district == district)
        .first()
    )


def set_user_location(
    session: Session, line_user_id: str, location_type: str, county: str, district: str
) -> tuple[bool, str, Location | None]:
    """
    Set user's home or work location.

    Args:
        session: database Session object
        line_user_id: LINE user ID
        location_type: "home" or "work"
        county: county name
        district: district name

    Returns:
        Tuple of (success, message, location)
    """
    # Validate location_type
    if location_type not in ["home", "work"]:
        return False, "無效的地點類型", None

    # Get or create user
    user = get_user_by_line_id(session, line_user_id)
    if not user:
        # Auto-create user for LIFF users (they must be authenticated by LINE)
        user = create_user_if_not_exists(session, line_user_id, display_name=None)

    # Get location
    location = get_location_by_county_district(session, county, district)
    if not location:
        return False, "地點不存在", None

    # Update user location
    if location_type == "home":
        user.home_location_id = location.id
    else:  # work
        user.work_location_id = location.id

    session.commit()
    session.refresh(user)

    return True, "地點設定成功", location
