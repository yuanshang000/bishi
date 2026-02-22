"""
API v1路由集成
"""

from fastapi import APIRouter

from app.api.v1 import auth, chapters, documents, quiz, chat, wrong_question
import logging
logger = logging.getLogger(__name__)
try:
    from app.api.v1 import ai_analysis
    _has_ai_analysis = True
except Exception as e:
    logger.warning(f"AI analysis module not available: {e}")
    _has_ai_analysis = False

# 创建API v1路由器
api_router = APIRouter(prefix="/api/v1")

# 注册所有子路由
api_router.include_router(auth.router)
api_router.include_router(chapters.router)
api_router.include_router(documents.router)
api_router.include_router(quiz.router)
api_router.include_router(chat.router)
api_router.include_router(wrong_question.router)
if _has_ai_analysis:
    api_router.include_router(ai_analysis.router, prefix="/ai", tags=["AI分析"])

__all__ = ["api_router"]
