"""
错题记录模型

定义错题记录数据表结构和关系
"""

from sqlalchemy import Column, Integer, String, Text, Float, DateTime, ForeignKey, Index
from sqlalchemy.orm import relationship, backref
from datetime import datetime

from app.core.database import Base


class WrongQuestion(Base):
    """
    错题记录模型

    记录学生做错的题目，用于错题重练和薄弱点分析
    """
    __tablename__ = "wrong_questions"

    # 主键
    id = Column(Integer, primary_key=True, index=True, autoincrement=True,
                comment="错题ID")

    # 外键
    user_id = Column(
        Integer,
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
        comment="用户ID"
    )
    quiz_record_id = Column(
        Integer,
        ForeignKey("quiz_records.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
        comment="练习记录ID"
    )
    chapter_id = Column(
        Integer,
        ForeignKey("chapters.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
        comment="章节ID"
    )
    section_id = Column(
        Integer,
        ForeignKey("sections.id", ondelete="CASCADE"),
        nullable=True,
        index=True,
        comment="节ID"
    )
    subsection_id = Column(
        Integer,
        ForeignKey("subsections.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
        comment="小目标ID"
    )

    # 题目信息
    question_type = Column(String(50), nullable=False, index=True,
                          comment="题目类型")
    question_data = Column(Text, nullable=False,
                          comment="题目内容（JSON格式）")

    # 答题信息
    user_answer = Column(Text, nullable=True, comment="用户答案")
    correct_answer = Column(Text, nullable=True, comment="正确答案")
    score = Column(Float, default=0.0, comment="得分（0-1）")

    # 知识点关联
    knowledge_point_ids = Column(
        Text,
        nullable=True,
        comment="关联知识点ID（JSON数组）"
    )

    # 状态信息
    is_mastered = Column(
        Integer,
        default=0,
        comment="是否已掌握（1=是，0=否）"
    )
    retry_count = Column(
        Integer,
        default=0,
        comment="重做次数"
    )
    last_retry_score = Column(
        Float,
        nullable=True,
        comment="最后一次重做得分"
    )
    last_retry_at = Column(
        DateTime,
        nullable=True,
        comment="最后重做时间"
    )

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

    subsection = relationship("SubSection", back_populates="wrong_questions")


    # 关系
    user = relationship("User", back_populates="wrong_questions")
    quiz_record = relationship("QuizRecord", backref=backref("wrong_questions", cascade="all, delete-orphan"))
    chapter = relationship("Chapter", backref=backref("wrong_questions", cascade="all, delete-orphan"))

    # 复合索引：用于查询用户某章节的错题
    __table_args__ = (
        Index('ix_wrong_questions_user_chapter', 'user_id', 'chapter_id'),
        Index('ix_wrong_questions_user_mastered', 'user_id', 'is_mastered'),
    )

    def __repr__(self):
        return f"<WrongQuestion(id={self.id}, user_id={self.user_id}, type={self.question_type})>"

    def to_dict(self):
        """转换为字典格式"""
        import json
        return {
            "id": self.id,
            "user_id": self.user_id,
            "quiz_record_id": self.quiz_record_id,
            "chapter_id": self.chapter_id,
            "question_type": self.question_type,
            "question_data": json.loads(self.question_data) if self.question_data else {},
            "user_answer": self.user_answer,
            "correct_answer": self.correct_answer,
            "score": self.score,
            "knowledge_point_ids": json.loads(self.knowledge_point_ids) if self.knowledge_point_ids else [],
            "is_mastered": bool(self.is_mastered),
            "retry_count": self.retry_count,
            "last_retry_score": self.last_retry_score,
            "last_retry_at": self.last_retry_at.isoformat() if self.last_retry_at else None,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }
