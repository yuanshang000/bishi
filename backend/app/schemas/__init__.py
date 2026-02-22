"""
Pydantic Schemas模块

导出所有数据验证模式
"""

from app.schemas.user import (
    UserBase,
    UserCreate,
    UserUpdate,
    UserResponse,
    UserLogin,
    Token,
    TokenData,
)

from app.schemas.chapter import (
    ChapterBase,
    ChapterCreate,
    ChapterUpdate,
    ChapterResponse,
)

from app.schemas.document import (
    DocumentBase,
    DocumentCreate,
    DocumentUpdate,
    DocumentResponse,
    DocumentUpload,
)

from app.schemas.quiz import (
    QuizBase,
    QuizCreate,
    QuizSubmit,
    QuizResponse,
    QuestionBase,
    QuizResult,
)

from app.schemas.chat import (
    ChatBase,
    ChatCreate,
    ChatResponse,
    ChatRequest,
    ChatMessage,
)

__all__ = [
    # User schemas
    "UserBase",
    "UserCreate",
    "UserUpdate",
    "UserResponse",
    "UserLogin",
    "Token",
    "TokenData",
    # Chapter schemas
    "ChapterBase",
    "ChapterCreate",
    "ChapterUpdate",
    "ChapterResponse",
    # Document schemas
    "DocumentBase",
    "DocumentCreate",
    "DocumentUpdate",
    "DocumentResponse",
    "DocumentUpload",
    # Quiz schemas
    "QuizBase",
    "QuizCreate",
    "QuizSubmit",
    "QuizResponse",
    "QuestionBase",
    "QuizResult",
    # Chat schemas
    "ChatBase",
    "ChatCreate",
    "ChatResponse",
    "ChatRequest",
    "ChatMessage",
]
