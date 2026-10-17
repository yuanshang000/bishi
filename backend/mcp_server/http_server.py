"""
MCP HTTP Server - 基于 HTTP API 的 MCP 服务
提供所有工具服务，通过 HTTP API 与主应用通信
"""

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import Dict, Any, Optional, List
import logging
import sys
import os
import uvicorn

# 添加项目路径并切换到项目根目录
project_root = os.path.join(os.path.dirname(__file__), '..')
os.chdir(project_root)
sys.path.insert(0, project_root)

# 导入数据库配置
from app.core.database import SessionLocal
from app.core.config import settings

# 导入 ORM 模型
from app.models.wrong_question import WrongQuestion
from app.models.quiz import QuizRecord
from app.models.chapter import Chapter
from app.models.section import Section
from app.models.subsection import SubSection
from app.models.user_word_stats import UserWordStats
from app.models.knowledge_point import KnowledgePoint

# 导入服务
from app.services.rag_service import rag_service
# 注意：不导入 llm_service，避免循环导入

# 导入 SQLAlchemy
from sqlalchemy import func, desc

logger = logging.getLogger(__name__)

# 创建 FastAPI 应用
app = FastAPI(
    title="MCP Tool Service",
    description="Model Context Protocol Tool Service - HTTP API",
    version="1.0.0"
)


# ==================== 请求模型 ====================

class ToolCallRequest(BaseModel):
    """工具调用请求"""
    name: str
    arguments: Dict[str, Any]


class ToolCallResponse(BaseModel):
    """工具调用响应"""
    success: bool
    result: Optional[Dict[str, Any]] = None
    error: Optional[str] = None


# ==================== API 路由 ====================

@app.get("/")
def root():
    """根路径"""
    return {
        "service": "MCP Tool Service",
        "version": "1.0.0",
        "status": "running"
    }


@app.get("/health")
def health_check():
    """健康检查"""
    return {"status": "healthy"}


@app.get("/tools")
def list_tools():
    """列出所有可用工具"""
    return {
        "tools": [
            {
                "name": "get_student_quiz_history",
                "description": "获取学生最近的测验历史记录"
            },
            {
                "name": "get_wrong_questions_by_subsection",
                "description": "获取指定小目标的错题记录"
            },
            {
                "name": "get_student_learning_progress",
                "description": "获取学生当前的学习进度"
            },
            {
                "name": "get_next_content",
                "description": "获取学生下一步应该学习的内容"
            },
            {
                "name": "get_student_weak_points",
                "description": "获取学生的薄弱知识点"
            },
            {
                "name": "search_course_content",
                "description": "搜索课程内容"
            },
            {
                "name": "generate_interactive_quiz",
                "description": "生成互动练习题"
            },
            {
                "name": "fetch_learning_data",
                "description": "获取学习数据"
            },
            {
                "name": "fetch_wrong_questions",
                "description": "获取错题数据"
            },
            {
                "name": "fetch_weak_knowledge_points",
                "description": "获取薄弱知识点数据"
            }
        ]
    }


@app.post("/call", response_model=ToolCallResponse)
def call_tool(request: ToolCallRequest):
    """
    调用工具
    
    这是 MCP 的核心接口，通过 HTTP POST 调用工具
    """
    logger.info(f"MCP HTTP Server received tool call: {request.name}")
    
    # 创建数据库会话
    db = SessionLocal()
    
    try:
        result = None
        
        # 数据查询工具
        if request.name == "get_student_quiz_history":
            result = _get_student_quiz_history(
                db=db,
                student_id=request.arguments["student_id"],
                limit=request.arguments.get("limit", 5)
            )
        
        elif request.name == "get_wrong_questions_by_subsection":
            result = _get_wrong_questions_by_subsection(
                db=db,
                student_id=request.arguments["student_id"],
                subsection_id=request.arguments["subsection_id"],
                limit=request.arguments.get("limit", 5)
            )
        
        elif request.name == "get_student_learning_progress":
            result = _get_student_learning_progress(
                db=db,
                student_id=request.arguments["student_id"]
            )
        
        elif request.name == "get_next_content":
            result = _get_next_content(
                db=db,
                student_id=request.arguments.get("student_id"),
                current_subsection_id=request.arguments.get("current_subsection_id")
            )
        
        elif request.name == "get_student_weak_points":
            result = _get_student_weak_points(
                db=db,
                student_id=request.arguments["student_id"]
            )
        
        # 内容检索工具
        elif request.name == "search_course_content":
            result = _search_course_content(
                query=request.arguments["query"],
                chapter_id=request.arguments.get("chapter_id"),
                top_k=request.arguments.get("top_k", 3)
            )
        
        # 练习生成工具
        elif request.name == "generate_interactive_quiz":
            result = _generate_interactive_quiz(
                db=db,
                topic=request.arguments["topic"],
                count=request.arguments.get("count", 3),
                quiz_type=request.arguments.get("quiz_type", "mixed"),
                difficulty=request.arguments.get("difficulty", "intermediate"),
                student_id=request.arguments.get("student_id")
            )
        
        # 数据访问工具
        elif request.name == "fetch_learning_data":
            result = _fetch_learning_data(
                db=db,
                student_id=request.arguments["student_id"],
                subsection_id=request.arguments.get("subsection_id")
            )
        
        elif request.name == "fetch_wrong_questions":
            result = _fetch_wrong_questions(
                db=db,
                student_id=request.arguments["student_id"],
                limit=request.arguments.get("limit", 10)
            )
        
        elif request.name == "fetch_weak_knowledge_points":
            result = _fetch_weak_knowledge_points(
                db=db,
                student_id=request.arguments["student_id"]
            )
        
        else:
            return ToolCallResponse(
                success=False,
                error=f"Unknown tool: {request.name}"
            )
        
        logger.info(f"Tool {request.name} executed successfully")
        return ToolCallResponse(success=True, result=result)
        
    except Exception as e:
        logger.error(f"Tool call failed: {e}", exc_info=True)
        return ToolCallResponse(success=False, error=str(e))
    finally:
        db.close()


# ==================== 工具实现函数 ====================
# (从原来的 server.py 复制所有工具实现函数)

def _get_student_quiz_history(db, student_id: int, limit: int = 5) -> List[Dict[str, Any]]:
    """获取学生最近的测验历史"""
    records = db.query(QuizRecord).filter(
        QuizRecord.user_id == student_id
    ).order_by(desc(QuizRecord.created_at)).limit(limit).all()
    
    return [
        {
            "quiz_id": r.id,
            "score": r.score,
            "total_questions": r.question_count,
            "quiz_type": r.quiz_type,
            "created_at": r.created_at.isoformat(),
            "chapter_id": r.chapter_id
        }
        for r in records
    ]


def _get_wrong_questions_by_subsection(db, student_id: int, subsection_id: int, limit: int = 5) -> List[Dict[str, Any]]:
    """获取指定小目标的错题"""
    wrong_questions = db.query(WrongQuestion).filter(
        WrongQuestion.user_id == student_id,
        WrongQuestion.subsection_id == subsection_id
    ).order_by(desc(WrongQuestion.created_at)).limit(limit).all()
    
    return [
        {
            "question_id": w.id,
            "question": w.question,
            "correct_answer": w.correct_answer,
            "user_answer": w.user_answer,
            "created_at": w.created_at.isoformat()
        }
        for w in wrong_questions
    ]


def _get_student_learning_progress(db, student_id: int) -> Dict[str, Any]:
    """获取学生当前的学习进度"""
    # 获取最近的学习记录
    recent_quiz = db.query(QuizRecord).filter(
        QuizRecord.user_id == student_id
    ).order_by(desc(QuizRecord.created_at)).first()
    
    # 获取错题统计
    wrong_count = db.query(WrongQuestion).filter(
        WrongQuestion.user_id == student_id
    ).count()
    
    return {
        "recent_quiz": {
            "quiz_id": recent_quiz.id if recent_quiz else None,
            "score": recent_quiz.score if recent_quiz else None,
            "created_at": recent_quiz.created_at.isoformat() if recent_quiz else None
        } if recent_quiz else None,
        "total_wrong_questions": wrong_count
    }


def _get_next_content(db, student_id: Optional[int], current_subsection_id: Optional[int]) -> Dict[str, Any]:
    """获取下一步学习内容"""
    if not current_subsection_id:
        # 获取第一个小目标
        first_subsection = db.query(SubSection).order_by(SubSection.id).first()
        if first_subsection:
            return {
                "subsection_id": first_subsection.id,
                "title": first_subsection.title,
                "content": first_subsection.content
            }
        return {"message": "没有找到学习内容"}
    
    # 获取下一个小目标
    next_subsection = db.query(SubSection).filter(
        SubSection.id > current_subsection_id
    ).order_by(SubSection.id).first()
    
    if next_subsection:
        return {
            "subsection_id": next_subsection.id,
            "title": next_subsection.title,
            "content": next_subsection.content
        }
    
    return {"message": "已完成所有内容"}


def _get_student_weak_points(db, student_id: int) -> List[Dict[str, Any]]:
    """获取学生的薄弱知识点"""
    # 统计错题最多的知识点
    weak_points = db.query(
        KnowledgePoint.name,
        func.count(WrongQuestion.id).label('wrong_count')
    ).join(
        WrongQuestion,
        KnowledgePoint.id == WrongQuestion.knowledge_point_id
    ).filter(
        WrongQuestion.user_id == student_id
    ).group_by(
        KnowledgePoint.id
    ).order_by(
        desc('wrong_count')
    ).limit(5).all()
    
    return [
        {
            "knowledge_point": wp.name,
            "wrong_count": wp.wrong_count
        }
        for wp in weak_points
    ]


def _search_course_content(query: str, chapter_id: Optional[int], top_k: int) -> List[Dict[str, Any]]:
    """搜索课程内容"""
    results = rag_service.search(
        query=query,
        chapter_id=chapter_id,
        top_k=top_k
    )
    
    return [
        {
            "content": r.get("content", ""),
            "metadata": r.get("metadata", {}),
            "score": r.get("score", 0)
        }
        for r in results
    ]


def _generate_interactive_quiz(db, topic: str, count: int, quiz_type: str, difficulty: str, student_id: Optional[int]) -> Dict[str, Any]:
    """生成互动练习题"""
    from app.tools.quiz_tools import generate_interactive_quiz
    
    result = generate_interactive_quiz(
        db=db,
        topic=topic,
        count=count,
        quiz_type=quiz_type,
        difficulty=difficulty,
        student_id=student_id
    )
    
    return result


def _fetch_learning_data(db, student_id: int, subsection_id: Optional[int]) -> Dict[str, Any]:
    """获取学习数据"""
    # 获取学习进度
    progress = _get_student_learning_progress(db, student_id)
    
    # 如果指定了小目标，获取详细内容
    if subsection_id:
        subsection = db.query(SubSection).filter(SubSection.id == subsection_id).first()
        if subsection:
            progress["subsection"] = {
                "id": subsection.id,
                "title": subsection.title,
                "content": subsection.content
            }
    
    return progress


def _fetch_wrong_questions(db, student_id: int, limit: int) -> List[Dict[str, Any]]:
    """获取错题数据"""
    wrong_questions = db.query(WrongQuestion).filter(
        WrongQuestion.user_id == student_id
    ).order_by(desc(WrongQuestion.created_at)).limit(limit).all()
    
    return [
        {
            "question_id": w.id,
            "question": w.question,
            "correct_answer": w.correct_answer,
            "user_answer": w.user_answer,
            "subsection_id": w.subsection_id,
            "created_at": w.created_at.isoformat()
        }
        for w in wrong_questions
    ]


def _fetch_weak_knowledge_points(db, student_id: int) -> List[Dict[str, Any]]:
    """获取薄弱知识点数据"""
    return _get_student_weak_points(db, student_id)


# ==================== 启动服务 ====================

if __name__ == "__main__":
    logger.info("Starting MCP HTTP Server on port 8001...")
    uvicorn.run(
        app,
        host="0.0.0.0",
        port=8001,
        log_level="info"
    )
