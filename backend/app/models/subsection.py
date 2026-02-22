"""
小目标模型 (SubSection)

定义小节下的小目标（子节）数据表结构和关系
"""

from sqlalchemy import Column, Integer, String, Text, DateTime, ForeignKey, Float
from sqlalchemy.orm import relationship
from datetime import datetime

from app.core.database import Base


class SubSection(Base):
    """
    小目标模型 (SubSection)
    
    对应具体的教学目标，如"1.1.1 掌握某些单词"
    """
    __tablename__ = "subsections"

    # 主键
    id = Column(Integer, primary_key=True, index=True, autoincrement=True, comment="小目标ID")

    # 外键
    section_id = Column(
        Integer,
        ForeignKey("sections.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
        comment="所属小节ID"
    )

    # 基本信息
    title = Column(String(200), nullable=False, comment="小目标标题（如：1.1.1 掌握核心词汇）")
    description = Column(Text, nullable=True, comment="目标描述")
    content = Column(Text, nullable=True, comment="具体的知识点内容（文本）")
    
    # 出题与考核要求
    requirements = Column(Text, nullable=True, comment="出题要求与结构化知识点（JSON格式）")
    user_friendly_requirements = Column(Text, nullable=True, comment="用户友好的出题要求描述")
    
    # 考核指标
    weight = Column(Float, default=0.0, comment="权重占比 (0-100)")
    passing_score = Column(Float, default=60.0, comment="合格分数")
    min_questions = Column(Integer, default=10, comment="最少训练题数")
    
    order = Column(Integer, default=0, comment="排序顺序")

    # 时间戳
    created_at = Column(
        DateTime,
        nullable=False,
        default=datetime.utcnow,
        comment="创建时间"
    )
    updated_at = Column(
        DateTime,
        nullable=False,
        default=datetime.utcnow,
        onupdate=datetime.utcnow,
        comment="更新时间"
    )

    # 关系
    section = relationship("Section", back_populates="subsections")
    quiz_records = relationship("QuizRecord", back_populates="subsection", cascade="all, delete-orphan")
    wrong_questions = relationship("WrongQuestion", back_populates="subsection")
    knowledge_points = relationship(
        "KnowledgePoint",
        back_populates="subsection",
        cascade="all, delete-orphan"
    )

    def __repr__(self):
        return f"<SubSection(id={self.id}, title='{self.title}')>"
