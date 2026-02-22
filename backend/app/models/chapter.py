"""
章节模型

定义课程章节数据表结构和关系
"""

from sqlalchemy import Column, Integer, String, Text, DateTime
from sqlalchemy.orm import relationship
from datetime import datetime

from app.core.database import Base


class Chapter(Base):
    """
    章节模型

    存储课程章节信息和元数据
    """
    __tablename__ = "chapters"

    # 主键
    id = Column(Integer, primary_key=True, index=True, autoincrement=True, comment="章节ID")

    # 章节信息
    chapter_number = Column(
        Integer,
        nullable=False,
        unique=True,
        index=True,
        comment="章节编号（唯一）"
    )
    title = Column(String(200), nullable=False, comment="章节标题")
    description = Column(Text, nullable=True, comment="章节描述")

    # 学习目标
    learning_objectives = Column(Text, nullable=True, comment="学习目标（JSON格式）")

    # 知识点
    key_points = Column(Text, nullable=True, comment="知识点列表（JSON格式）")

    # 元数据
    word_count = Column(Integer, default=0, comment="词汇量")
    difficulty_level = Column(String(20), default="intermediate", comment="难度等级")

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
    sections = relationship(
        "Section",
        back_populates="chapter",
        cascade="all, delete-orphan",
        order_by="Section.order"
    )
    documents = relationship(
        "CourseDocument",
        back_populates="chapter",
        cascade="all, delete-orphan",
        lazy="dynamic"
    )
    quiz_records = relationship(
        "QuizRecord",
        back_populates="chapter",
        cascade="all, delete-orphan",
        lazy="dynamic"
    )
    chat_histories = relationship(
        "ChatHistory",
        back_populates="chapter",
        cascade="all, delete-orphan",
        lazy="dynamic"
    )

    def __repr__(self):
        return f"<Chapter(id={self.id}, number={self.chapter_number}, title='{self.title}')>"

    def to_dict(self):
        """转换为字典格式"""
        return {
            "id": self.id,
            "chapter_number": self.chapter_number,
            "title": self.title,
            "description": self.description,
            "learning_objectives": self.learning_objectives,
            "key_points": self.key_points,
            "word_count": self.word_count,
            "difficulty_level": self.difficulty_level,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }
