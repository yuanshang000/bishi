
from sqlalchemy import Column, Integer, String, Float, DateTime, ForeignKey, Enum
from sqlalchemy.orm import relationship
from datetime import datetime
import enum

from app.core.database import Base

class KnowledgePointType(str, enum.Enum):
    WORD = "word"
    GRAMMAR = "grammar"
    PHRASE = "phrase"
    OTHER = "other"

class KnowledgePoint(Base):
    """
    知识点模型 (KnowledgePoint)
    
    用于精细化追踪每个单词、语法点、短语的掌握情况
    """
    __tablename__ = "knowledge_points"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    
    # 关联的小节
    subsection_id = Column(Integer, ForeignKey("subsections.id", ondelete="CASCADE"), nullable=False, index=True)
    
    # 内容与类型
    content = Column(String(255), nullable=False, comment="知识点内容(单词/短语/语法点)")
    type = Column(String(50), nullable=False, default="word", comment="类型: word, grammar, phrase, other")
    
    # 智能分批策略字段
    priority_score = Column(Float, default=0.0, comment="优先级分数，越小优先级越高")
    consecutive_errors = Column(Integer, default=0, comment="连续做错次数")
    last_reviewed_at = Column(DateTime, default=None, nullable=True, comment="上次复习时间")
    
    # 统计信息 (可选)
    total_attempts = Column(Integer, default=0, comment="总练习次数")
    correct_attempts = Column(Integer, default=0, comment="做对次数")

    # 关系
    subsection = relationship("SubSection", back_populates="knowledge_points")

    def __repr__(self):
        return f"<KnowledgePoint(content='{self.content}', score={self.priority_score})>"
