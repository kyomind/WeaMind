from datetime import datetime

from sqlalchemy import Column, DateTime, Integer, String

from app.core.database import Base


class User(Base):
    """
    用戶資料庫模型
    """

    __tablename__ = "user"

    id = Column(Integer, primary_key=True, index=True)
    line_user_id = Column(String, unique=True, index=True, nullable=False)
    display_name = Column(String, nullable=True)
    quota = Column(Integer, default=5)  # 預設每日查詢額度
    quota_used = Column(Integer, default=0)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
