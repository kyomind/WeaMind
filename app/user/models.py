from sqlalchemy import Column, Integer, String, DateTime
from sqlalchemy.ext.declarative import declarative_base
from datetime import datetime

Base = declarative_base()

class User(Base):
    """
    用戶資料庫模型
    
    定義用戶在資料庫中的結構，用於儲存用戶相關資訊
    """
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    line_user_id = Column(String, unique=True, index=True, nullable=False)
    display_name = Column(String, nullable=True)
    quota = Column(Integer, default=5)  # 預設每日查詢額度
    quota_used = Column(Integer, default=0)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
