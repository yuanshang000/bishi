
from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, Index
from datetime import datetime
from app.core.database import Base

class UserWordStats(Base):
    __tablename__ = "user_word_stats"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    subsection_id = Column(Integer, ForeignKey("subsections.id", ondelete="CASCADE"), nullable=False, index=True)
    word = Column(String(255), nullable=False, index=True)
    count = Column(Integer, default=0, comment="练习计数")
    
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    __table_args__ = (
        Index('ix_user_word_stats_user_subsection_word', 'user_id', 'subsection_id', 'word', unique=True),
    )
