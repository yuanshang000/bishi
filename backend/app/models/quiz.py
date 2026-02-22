"""
练习记录模型

定义练习记录数据表结构和关系
"""

from sqlalchemy import Column, Integer, String, Text, Float, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from datetime import datetime

from app.core.database import Base


class QuizRecord(Base):
    """
    练习记录模型

    存储学生的练习答题记录和成绩
    """
    __tablename__ = "quiz_records"

    # 主键
    id = Column(Integer, primary_key=True, index=True, autoincrement=True, comment="记录ID")

    # 外键
    user_id = Column(
        Integer,
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
        comment="用户ID"
    )
    chapter_id = Column(
        Integer,
        ForeignKey("chapters.id", ondelete="CASCADE"),
        nullable=True,  # 随机练习和综合练习不需要章节
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
        ForeignKey("subsections.id", ondelete="CASCADE"),
        nullable=True,
        index=True,
        comment="小目标ID"
    )

    # 练习信息
    practice_mode = Column(
        String(20),
        nullable=False,
        default="chapter",
        index=True,
        comment="练习方式（chapter=章节练习, random=随机练习, comprehensive=综合练习）"
    )
    quiz_type = Column(
        String(50),
        nullable=False,
        index=True,
        comment="练习类型（choice/blank/translation等）"
    )
    difficulty = Column(
        String(20),
        default="medium",
        comment="难度等级（low=低, medium=中/四级, high=高/六级）"
    )
    question_count = Column(Integer, default=0, comment="题目总数")

    # 答题数据
    questions = Column(Text, nullable=True, comment="题目列表（JSON格式）")
    user_answers = Column(Text, nullable=True, comment="用户答案（JSON格式）")
    correct_answers = Column(Text, nullable=True, comment="正确答案（JSON格式）")
    results = Column(Text, nullable=True, comment="详细批改结果（JSON格式，包含每道题的反馈）")

    # 成绩统计
    score = Column(Float, default=0.0, comment="得分")
    accuracy = Column(Float, default=0.0, comment="正确率（0-100）")
    time_spent = Column(Integer, default=0, comment="用时（秒）")

    # 知识点关联
    knowledge_point_ids = Column(
        Text,
        nullable=True,
        comment="关联的知识点ID列表（JSON数组）"
    )

    # 状态
    is_completed = Column(Integer, default=0, comment="是否完成（1=是，0=否）")

    # 时间戳
    started_at = Column(DateTime, nullable=True, comment="开始时间")
    completed_at = Column(DateTime, nullable=True, comment="完成时间")
    created_at = Column(
        DateTime,
        nullable=False,
        default=datetime.utcnow,
        comment="创建时间"
    )

    # 关系
    user = relationship("User", back_populates="quiz_records")
    chapter = relationship("Chapter", back_populates="quiz_records")
    subsection = relationship("SubSection", back_populates="quiz_records")

    def __repr__(self):
        return f"<QuizRecord(id={self.id}, user_id={self.user_id}, score={self.score})>"

    def to_dict(self):
        """转换为字典格式"""
        import json

        # 解析JSON字段
        questions = None
        if self.questions:
            try:
                questions = json.loads(self.questions) if isinstance(self.questions, str) else self.questions
            except:
                questions = []

        return {
            "id": self.id,
            "user_id": self.user_id,
            "chapter_id": self.chapter_id,
            "practice_mode": self.practice_mode,  # 添加练习方式
            "quiz_type": self.quiz_type,
            "question_count": self.question_count,
            "questions": questions,  # 添加questions字段
            "score": self.score,
            "accuracy": self.accuracy,
            "time_spent": self.time_spent,
            "is_completed": bool(self.is_completed),
            "started_at": self.started_at.isoformat() if self.started_at else None,
            "completed_at": self.completed_at.isoformat() if self.completed_at else None,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }
