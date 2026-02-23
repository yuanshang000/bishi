
from sqlalchemy import Column, Integer, String, Float, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from datetime import datetime
from app.core.database import Base

class UserKnowledgePointStats(Base):
    """
    用户知识点掌握情况统计表
    
    用于记录每个用户对每个知识点的掌握程度，区分不同用户的学习进度。
    """
    __tablename__ = "user_knowledge_stats"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    
    # 用户关联
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    
    # 知识点关联
    knowledge_point_id = Column(Integer, ForeignKey("knowledge_points.id", ondelete="CASCADE"), nullable=False, index=True)
    
    # 统计数据
    total_attempts = Column(Integer, default=0, comment="总练习次数")
    correct_attempts = Column(Integer, default=0, comment="做对次数")
    consecutive_errors = Column(Integer, default=0, comment="连续做错次数")
    consecutive_corrects = Column(Integer, default=0, comment="连续做对次数")
    
    # 掌握度评分 (0-100)
    mastery_score = Column(Float, default=0.0, comment="掌握度评分")
    
    # 时间戳
    last_reviewed_at = Column(DateTime, default=None, nullable=True, comment="上次复习时间")
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    # 关系
    user = relationship("User")
    knowledge_point = relationship("KnowledgePoint")

    def __repr__(self):
        return f"<UserKnowledgePointStats(user_id={self.user_id}, kp_id={self.knowledge_point_id}, score={self.mastery_score})>"
