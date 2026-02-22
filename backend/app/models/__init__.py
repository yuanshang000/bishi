"""
数据库模型模块

导出所有数据模型供其他模块使用
"""

from app.models.user import User
from app.models.chapter import Chapter
from app.models.section import Section
from app.models.subsection import SubSection
from app.models.document import CourseDocument
from app.models.quiz import QuizRecord
from app.models.chat import ChatHistory
from app.models.wrong_question import WrongQuestion
from app.models.knowledge_point import KnowledgePoint
from app.models.user_word_stats import UserWordStats

__all__ = [
    "User",
    "Chapter",
    "Section",
    "SubSection",
    "CourseDocument",
    "QuizRecord",
    "ChatHistory",
    "WrongQuestion",
    "KnowledgePoint",
    "UserWordStats",
]
