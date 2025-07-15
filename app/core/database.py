"""Database connection and session management for the app."""

import typing

from sqlalchemy import create_engine
from sqlalchemy.orm import DeclarativeBase, Session, sessionmaker
from sqlalchemy.pool import StaticPool

from app.core.config import settings

# 使用簡化的配置結構
DATABASE_URL = settings.database_url

connect_args = {}
poolclass = None
if DATABASE_URL.startswith("sqlite"):  # pragma: no cover - simple check
    connect_args = {"check_same_thread": False}
    poolclass = StaticPool

engine = create_engine(
    DATABASE_URL,
    echo=settings.DEBUG,
    connect_args=connect_args,
    poolclass=poolclass,
)
SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False, future=True)


class Base(DeclarativeBase):
    """SQLAlchemy base class for all ORM models."""

    pass


def get_db() -> typing.Generator[Session, None, None]:
    """
    Create a database Session.

    For FastAPI dependency injection
    Usage: Add Depends(get_db) in your route

    Returns
        A database Session
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
