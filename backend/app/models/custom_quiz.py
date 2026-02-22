"""
自定义出题练习记录模型

专门用于存储智能问答模式（Chat Quiz Mode）下的练习历史
独立于练习中心的 QuizRecord，以适应灵活多变的题型和数据结构
"""

from sqlalchemy import Column, Integer, String, Text, Float, DateTime, ForeignKey, Boolean
from sqlalchemy.orm import relationship
from datetime import datetime
import json

from app.core.database import Base


class CustomQuizRecord(Base):
    """
    自定义出题练习记录模型
    
    存储智能问答模式生成的题目、用户答案和结果
    """
    __tablename__ = "custom_quiz_records"

    # 主键
    id = Column(Integer, primary_key=True, index=True, autoincrement=True, comment="记录ID")

    # 关联用户
    user_id = Column(
        Integer,
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
        comment="用户ID"
    )

    # 关联聊天记录 (可选，用于回溯)
    chat_history_id = Column(
        Integer,
        ForeignKey("chat_histories.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
        comment="关联的聊天记录ID"
    )

    # 关联章节 (可选，如果有明确章节上下文)
    chapter_id = Column(
        Integer,
        ForeignKey("chapters.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
        comment="关联章节ID"
    )

    # 题目信息
    topic = Column(Text, nullable=True, comment="出题主题/提示词")
    quiz_type = Column(String(50), default="mixed", comment="题目类型(choice/blank/translation/mixed)")
    difficulty = Column(String(20), default="intermediate", comment="难度")
    question_count = Column(Integer, default=0, comment="题目数量")
    
    # 核心数据 (JSON存储)
    questions_data = Column(Text, nullable=False, comment="题目数据JSON")
    user_answers = Column(Text, nullable=True, comment="用户答案JSON")
    results_data = Column(Text, nullable=True, comment="判题结果JSON")
    
    # 统计
    score = Column(Float, default=0.0, comment="得分")
    is_completed = Column(Boolean, default=False, comment="是否完成")
    
    # 时间
    created_at = Column(DateTime, default=datetime.utcnow, comment="创建时间")
    completed_at = Column(DateTime, nullable=True, comment="完成时间")

    # 关系
    user = relationship("User", backref="custom_quiz_records")
    chat_history = relationship("ChatHistory", backref="custom_quiz_records")
    chapter = relationship("Chapter")

    def __repr__(self):
        return f"<CustomQuizRecord(id={self.id}, user_id={self.user_id}, topic='{self.topic[:20]}...')>"

    def to_dict(self):
        """转换为字典格式"""
        questions = []
        answers = {}
        results = {}
        
        if self.questions_data:
            try:
                questions = json.loads(self.questions_data)
            except:
                pass
                
        if self.user_answers:
            try:
                answers = json.loads(self.user_answers)
            except:
                pass
                
        if self.results_data:
            try:
                results = json.loads(self.results_data)
            except:
                pass

        return {
            "id": self.id,
            "user_id": self.user_id,
            "chat_history_id": self.chat_history_id,
            "chapter_id": self.chapter_id,
            "topic": self.topic,
            "quiz_type": self.quiz_type,
            "difficulty": self.difficulty,
            "question_count": self.question_count,
            "questions": questions,
            "user_answers": answers,
            "results": results,
            "score": self.score,
            "is_completed": self.is_completed,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "completed_at": self.completed_at.isoformat() if self.completed_at else None,
        }
