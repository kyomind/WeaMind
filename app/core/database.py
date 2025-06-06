import typing

from sqlalchemy import create_engine
from sqlalchemy.orm import DeclarativeBase, Session, sessionmaker

from app.core.config import settings

DATABASE_URL = (
    settings.DATABASE_URL
    or f"postgresql+psycopg2://{settings.POSTGRES_USER}:{settings.POSTGRES_PASSWORD}@{settings.POSTGRES_HOST}/{settings.POSTGRES_DB}"
)

engine = create_engine(DATABASE_URL, echo=settings.DEBUG)
SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False, future=True)


class Base(DeclarativeBase):
    pass


def get_db() -> typing.Generator[Session, None, None]:
    """
    建立資料庫連線 Session

    FastAPI 依賴注入用
    用法：在路由中加上 Depends(get_db)

    Returns:
        一個資料庫 Session 物件，可用於操作資料庫
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
