"""
MCP Server - Model Context Protocol Service
提供所有工具服务，通过 MCP 协议与主应用通信
"""

from mcp.server import Server
from mcp.types import Tool, TextContent
import asyncio
import logging
import json
import sys
import os
from typing import List, Dict, Any, Optional

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
from app.services.llm_service import llm_service

# 导入 SQLAlchemy
from sqlalchemy import func, desc

logger = logging.getLogger(__name__)

# 创建 MCP Server 实例
server = Server("education-tools")


@server.list_tools()
async def list_tools() -> List[Tool]:
    """
    列出所有可用的工具
    """
    return [
        # 数据查询工具
        Tool(
            name="get_student_quiz_history",
            description="获取学生最近的测验历史记录，包括分数、涉及的章节等信息。",
            inputSchema={
                "type": "object",
                "properties": {
                    "student_id": {
                        "type": "integer",
                        "description": "学生的用户ID"
                    },
                    "limit": {
                        "type": "integer",
                        "description": "返回记录数量限制，默认为5"
                    }
                },
                "required": ["student_id"]
            }
        ),
        Tool(
            name="get_wrong_questions_by_subsection",
            description="获取指定小目标（subsection）的错题记录，用于分析痛点和针对性出题。",
            inputSchema={
                "type": "object",
                "properties": {
                    "student_id": {
                        "type": "integer",
                        "description": "学生的用户ID"
                    },
                    "subsection_id": {
                        "type": "integer",
                        "description": "小目标ID (subsection ID)"
                    },
                    "limit": {
                        "type": "integer",
                        "description": "返回错题数量限制，默认为5"
                    }
                },
                "required": ["student_id", "subsection_id"]
            }
        ),
        Tool(
            name="get_student_learning_progress",
            description="获取学生当前的学习进度，包括正在学习的章节和小节信息。",
            inputSchema={
                "type": "object",
                "properties": {
                    "student_id": {
                        "type": "integer",
                        "description": "学生的用户ID"
                    }
                },
                "required": ["student_id"]
            }
        ),
        Tool(
            name="get_next_content",
            description="获取学生下一阶段的学习内容。如果只提供student_id，会自动查找最新进度并推荐。",
            inputSchema={
                "type": "object",
                "properties": {
                    "current_subsection_id": {
                        "type": "integer",
                        "description": "当前刚完成的小目标ID (可选)"
                    },
                    "student_id": {
                        "type": "integer",
                        "description": "学生ID (推荐使用)"
                    }
                },
                "required": []
            }
        ),
        Tool(
            name="get_student_weak_points",
            description="分析学生的薄弱点，返回平均分最低的几个领域及相关错题统计。",
            inputSchema={
                "type": "object",
                "properties": {
                    "student_id": {
                        "type": "integer",
                        "description": "学生的用户ID"
                    }
                },
                "required": ["student_id"]
            }
        ),
        # 内容检索工具
        Tool(
            name="search_course_content",
            description="从课程内容的向量数据库中检索相关知识。可以根据关键词或指定章节进行搜索。",
            inputSchema={
                "type": "object",
                "properties": {
                    "query": {
                        "type": "string",
                        "description": "搜索关键词或问题描述"
                    },
                    "chapter_id": {
                        "type": "integer",
                        "description": "指定章节ID进行过滤（可选）"
                    },
                    "top_k": {
                        "type": "integer",
                        "description": "返回结果数量（可选，默认3）"
                    }
                },
                "required": ["query"]
            }
        ),
        # 练习生成工具
        Tool(
            name="generate_interactive_quiz",
            description="Generate interactive quiz based on user topic/prompt. Use this when user explicitly asks to generate a quiz or is in Quiz Mode.",
            inputSchema={
                "type": "object",
                "properties": {
                    "topic": {
                        "type": "string",
                        "description": "User's topic or prompt for the quiz."
                    },
                    "count": {
                        "type": "integer",
                        "description": "Number of questions to generate (default: 3)."
                    },
                    "quiz_type": {
                        "type": "string",
                        "description": "Type of quiz (mixed, choice, blank, etc.) (default: mixed)."
                    },
                    "difficulty": {
                        "type": "string",
                        "description": "Difficulty level (easy, intermediate, hard) (default: intermediate)."
                    },
                    "student_id": {
                        "type": "integer",
                        "description": "Student ID."
                    }
                },
                "required": ["topic"]
            }
        ),
        # 数据访问工具（data_access）
        Tool(
            name="fetch_learning_data",
            description="获取学生的学习数据，包括练习记录、分数等信息。",
            inputSchema={
                "type": "object",
                "properties": {
                    "student_id": {
                        "type": "integer",
                        "description": "学生ID"
                    },
                    "subsection_id": {
                        "type": "integer",
                        "description": "小目标ID（可选）"
                    }
                },
                "required": ["student_id"]
            }
        ),
        Tool(
            name="fetch_wrong_questions",
            description="获取学生的错题记录。",
            inputSchema={
                "type": "object",
                "properties": {
                    "student_id": {
                        "type": "integer",
                        "description": "学生ID"
                    },
                    "limit": {
                        "type": "integer",
                        "description": "返回数量限制（可选，默认10）"
                    }
                },
                "required": ["student_id"]
            }
        ),
        Tool(
            name="fetch_weak_knowledge_points",
            description="获取学生的薄弱知识点。",
            inputSchema={
                "type": "object",
                "properties": {
                    "student_id": {
                        "type": "integer",
                        "description": "学生ID"
                    }
                },
                "required": ["student_id"]
            }
        )
    ]


@server.call_tool()
async def call_tool(name: str, arguments: Dict[str, Any]) -> List[TextContent]:
    """
    执行工具调用
    """
    logger.info(f"MCP Server received tool call: {name} with arguments: {arguments}")
    
    # 创建数据库会话
    db = SessionLocal()
    
    try:
        result = None
        
        # 数据查询工具
        if name == "get_student_quiz_history":
            result = _get_student_quiz_history(
                db=db,
                student_id=arguments["student_id"],
                limit=arguments.get("limit", 5)
            )
        
        elif name == "get_wrong_questions_by_subsection":
            result = _get_wrong_questions_by_subsection(
                db=db,
                student_id=arguments["student_id"],
                subsection_id=arguments["subsection_id"],
                limit=arguments.get("limit", 5)
            )
        
        elif name == "get_student_learning_progress":
            result = _get_student_learning_progress(
                db=db,
                student_id=arguments["student_id"]
            )
        
        elif name == "get_next_content":
            result = _get_next_content(
                db=db,
                student_id=arguments.get("student_id"),
                current_subsection_id=arguments.get("current_subsection_id")
            )
        
        elif name == "get_student_weak_points":
            result = _get_student_weak_points(
                db=db,
                student_id=arguments["student_id"]
            )
        
        # 内容检索工具
        elif name == "search_course_content":
            result = _search_course_content(
                query=arguments["query"],
                chapter_id=arguments.get("chapter_id"),
                top_k=arguments.get("top_k", 3)
            )
        
        # 练习生成工具
        elif name == "generate_interactive_quiz":
            result = _generate_interactive_quiz(
                db=db,
                topic=arguments["topic"],
                count=arguments.get("count", 3),
                quiz_type=arguments.get("quiz_type", "mixed"),
                difficulty=arguments.get("difficulty", "intermediate"),
                student_id=arguments.get("student_id")
            )
        
        # 数据访问工具
        elif name == "fetch_learning_data":
            result = _fetch_learning_data(
                db=db,
                student_id=arguments["student_id"],
                subsection_id=arguments.get("subsection_id")
            )
        
        elif name == "fetch_wrong_questions":
            result = _fetch_wrong_questions(
                db=db,
                student_id=arguments["student_id"],
                limit=arguments.get("limit", 10)
            )
        
        elif name == "fetch_weak_knowledge_points":
            result = _fetch_weak_knowledge_points(
                db=db,
                student_id=arguments["student_id"]
            )
        
        else:
            result = {"error": f"Unknown tool: {name}"}
        
        # 返回结果
        result_text = json.dumps(result, ensure_ascii=False, indent=2)
        logger.info(f"MCP Server tool call successful")
        
        return [TextContent(
            type="text",
            text=result_text
        )]
        
    except Exception as e:
        logger.error(f"MCP Server tool call failed: {e}", exc_info=True)
        return [TextContent(
            type="text",
            text=json.dumps({"error": str(e)}, ensure_ascii=False)
        )]
    finally:
        db.close()


# ==================== 直接调用接口 ====================

def handle_tool_call(name: str, arguments: Dict[str, Any]) -> Any:
    """
    直接调用工具（不通过 MCP 协议）
    用于 MCP Orchestrator 直接调用
    
    Args:
        name: 工具名称
        arguments: 工具参数
        
    Returns:
        工具执行结果（字典格式）
    """
    logger.info(f"MCP Server direct tool call: {name} with arguments: {arguments}")
    
    # 创建数据库会话
    db = SessionLocal()
    
    try:
        result = None
        
        # 数据查询工具
        if name == "get_student_quiz_history":
            result = _get_student_quiz_history(
                db=db,
                student_id=arguments["student_id"],
                limit=arguments.get("limit", 5)
            )
        
        elif name == "get_wrong_questions_by_subsection":
            result = _get_wrong_questions_by_subsection(
                db=db,
                student_id=arguments["student_id"],
                subsection_id=arguments["subsection_id"],
                limit=arguments.get("limit", 5)
            )
        
        elif name == "get_student_learning_progress":
            result = _get_student_learning_progress(
                db=db,
                student_id=arguments["student_id"]
            )
        
        elif name == "get_next_content":
            result = _get_next_content(
                db=db,
                student_id=arguments.get("student_id"),
                current_subsection_id=arguments.get("current_subsection_id")
            )
        
        elif name == "get_student_weak_points":
            result = _get_student_weak_points(
                db=db,
                student_id=arguments["student_id"]
            )
        
        # 内容检索工具
        elif name == "search_course_content":
            result = _search_course_content(
                query=arguments["query"],
                chapter_id=arguments.get("chapter_id"),
                top_k=arguments.get("top_k", 3)
            )
        
        # 练习生成工具
        elif name == "generate_interactive_quiz":
            result = _generate_interactive_quiz(
                db=db,
                topic=arguments["topic"],
                count=arguments.get("count", 3),
                quiz_type=arguments.get("quiz_type", "mixed"),
                difficulty=arguments.get("difficulty", "intermediate"),
                student_id=arguments.get("student_id")
            )
        
        # 数据访问工具
        elif name == "fetch_learning_data":
            result = _fetch_learning_data(
                db=db,
                student_id=arguments["student_id"],
                subsection_id=arguments.get("subsection_id")
            )
        
        elif name == "fetch_wrong_questions":
            result = _fetch_wrong_questions(
                db=db,
                student_id=arguments["student_id"],
                limit=arguments.get("limit", 10)
            )
        
        elif name == "fetch_weak_knowledge_points":
            result = _fetch_weak_knowledge_points(
                db=db,
                student_id=arguments["student_id"]
            )
        
        else:
            result = {"error": f"Unknown tool: {name}"}
        
        logger.info(f"MCP Server direct tool call successful")
        return result
        
    except Exception as e:
        logger.error(f"MCP Server direct tool call failed: {e}", exc_info=True)
        return {"error": str(e)}
    finally:
        db.close()


# ==================== 工具实现函数 ====================

def _get_student_quiz_history(db, student_id: int, limit: int = 5) -> List[Dict[str, Any]]:
    """获取学生最近的测验历史"""
    records = db.query(QuizRecord).filter(
        QuizRecord.user_id == student_id
    ).order_by(desc(QuizRecord.created_at)).limit(limit).all()
    
    history = []
    for record in records:
        context = "Unknown"
        if record.subsection_id:
            sub = db.query(SubSection).filter(SubSection.id == record.subsection_id).first()
            if sub:
                section = db.query(Section).filter(Section.id == sub.section_id).first()
                chapter = db.query(Chapter).filter(Chapter.id == section.chapter_id).first()
                context = f"{chapter.title} - {section.title} - {sub.title}"
        
        history.append({
            "id": record.id,
            "score": record.score,
            "context": context,
            "time": record.created_at.isoformat()
        })
    
    return history


def _get_wrong_questions_by_subsection(db, student_id: int, subsection_id: int, limit: int = 5) -> List[Dict[str, Any]]:
    """获取指定小目标的错题记录"""
    wrong_questions = db.query(WrongQuestion).filter(
        WrongQuestion.user_id == student_id,
        WrongQuestion.subsection_id == subsection_id
    ).order_by(desc(WrongQuestion.retry_count)).limit(limit).all()
    
    return [
        {
            "id": wq.id,
            "question_type": wq.question_type,
            "retry_count": wq.retry_count,
            "last_retry_time": wq.updated_at.isoformat() if wq.updated_at else None
        }
        for wq in wrong_questions
    ]


def _get_student_learning_progress(db, student_id: int) -> Dict[str, Any]:
    """获取学生当前的学习进度"""
    # 获取最近的练习记录
    recent_record = db.query(QuizRecord).filter(
        QuizRecord.user_id == student_id
    ).order_by(desc(QuizRecord.created_at)).first()
    
    if not recent_record:
        return {
            "current_chapter": None,
            "current_section": None,
            "current_subsection": None,
            "progress_percentage": 0
        }
    
    # 获取章节信息
    if recent_record.subsection_id:
        sub = db.query(SubSection).filter(SubSection.id == recent_record.subsection_id).first()
        if sub:
            section = db.query(Section).filter(Section.id == sub.section_id).first()
            chapter = db.query(Chapter).filter(Chapter.id == section.chapter_id).first()
            
            return {
                "current_chapter": chapter.title if chapter else None,
                "current_section": section.title if section else None,
                "current_subsection": sub.title if sub else None,
                "progress_percentage": 0  # 需要计算
            }
    
    return {
        "current_chapter": None,
        "current_section": None,
        "current_subsection": None,
        "progress_percentage": 0
    }


def _get_next_content(db, student_id: Optional[int] = None, current_subsection_id: Optional[int] = None) -> Dict[str, Any]:
    """获取学生下一阶段的学习内容"""
    if current_subsection_id:
        # 获取当前小节的下一个
        current_sub = db.query(SubSection).filter(SubSection.id == current_subsection_id).first()
        if current_sub:
            next_sub = db.query(SubSection).filter(
                SubSection.section_id == current_sub.section_id,
                SubSection.order > current_sub.order
            ).order_by(SubSection.order).first()
            
            if next_sub:
                return {
                    "next_subsection": {
                        "id": next_sub.id,
                        "title": next_sub.title
                    }
                }
    
    return {"next_subsection": None}


def _get_student_weak_points(db, student_id: int) -> List[Dict[str, Any]]:
    """分析学生的薄弱点"""
    # 查询所有练习记录
    records = db.query(QuizRecord).filter(
        QuizRecord.user_id == student_id
    ).all()
    
    # 按小节分组统计
    subsection_stats = {}
    for record in records:
        if record.subsection_id:
            if record.subsection_id not in subsection_stats:
                subsection_stats[record.subsection_id] = {
                    "total_score": 0,
                    "count": 0
                }
            subsection_stats[record.subsection_id]["total_score"] += record.score or 0
            subsection_stats[record.subsection_id]["count"] += 1
    
    # 计算平均分并排序
    weak_points = []
    for sub_id, stats in subsection_stats.items():
        avg_score = stats["total_score"] / stats["count"] if stats["count"] > 0 else 0
        sub = db.query(SubSection).filter(SubSection.id == sub_id).first()
        if sub:
            weak_points.append({
                "subsection_id": sub_id,
                "subsection_title": sub.title,
                "avg_score": avg_score,
                "count": stats["count"]
            })
    
    # 按平均分排序，返回最低的几个
    weak_points.sort(key=lambda x: x["avg_score"])
    return weak_points[:5]


def _search_course_content(query: str, chapter_id: Optional[int] = None, top_k: int = 3) -> List[Dict[str, Any]]:
    """检索课程内容向量数据库"""
    results = rag_service.search(query=query, chapter_id=chapter_id, top_k=top_k)
    
    formatted_results = []
    for res in results:
        formatted_results.append({
            "content": res["content"],
            "title": res["metadata"].get("title", "Unknown"),
            "doc_type": res["metadata"].get("doc_type", "unknown"),
            "relevance": res.get("score", 0)
        })
    
    return formatted_results


def _generate_interactive_quiz(db, topic: str, count: int = 3, quiz_type: str = "mixed", difficulty: str = "intermediate", student_id: Optional[int] = None) -> Dict[str, Any]:
    """生成互动练习题"""
    import re
    
    # 检查章节引用
    chapter_ref_match = re.search(r'【参考：(.*?)】', topic)
    
    search_query = topic
    target_subsection = None
    
    if chapter_ref_match:
        search_query = chapter_ref_match.group(1).strip()
    else:
        search_query = topic.strip()
    
    # 查找小节
    target_subsection = db.query(SubSection).filter(SubSection.title == search_query).first()
    
    context = ""
    used_docs = []
    
    if target_subsection:
        context, used_docs, _ = rag_service.get_context_for_subsection(
            subsection_id=target_subsection.id,
            max_length=3000
        )
    
    if not context:
        context, used_docs, _ = rag_service.get_context_for_query(query=search_query, max_length=3000)
    
    if not context:
        context = f"Topic/Prompt: {topic}"
    
    # 生成题目
    questions = llm_service.generate_custom_quiz(
        context=context,
        quiz_type=quiz_type,
        count=count,
        difficulty=difficulty
    )
    
    return {
        "generate_interactive_quiz_response": {
            "count": len(questions),
            "questions": questions,
            "topic": topic,
            "quiz_id": 0,
            "quiz_type": quiz_type,
            "difficulty": difficulty
        }
    }


def _fetch_learning_data(db, student_id: int, subsection_id: Optional[int] = None) -> List[Dict[str, Any]]:
    """获取学生的学习数据"""
    query = db.query(QuizRecord).filter(QuizRecord.user_id == student_id)
    
    if subsection_id:
        query = query.filter(QuizRecord.subsection_id == subsection_id)
    
    records = query.order_by(desc(QuizRecord.created_at)).limit(10).all()
    
    return [
        {
            "id": r.id,
            "score": r.score,
            "subsection_id": r.subsection_id,
            "created_at": r.created_at.isoformat()
        }
        for r in records
    ]


def _fetch_wrong_questions(db, student_id: int, limit: int = 10) -> List[Dict[str, Any]]:
    """获取学生的错题记录"""
    wrong_questions = db.query(WrongQuestion).filter(
        WrongQuestion.user_id == student_id
    ).order_by(desc(WrongQuestion.created_at)).limit(limit).all()
    
    return [
        {
            "id": wq.id,
            "question_type": wq.question_type,
            "subsection_id": wq.subsection_id,
            "retry_count": wq.retry_count,
            "created_at": wq.created_at.isoformat()
        }
        for wq in wrong_questions
    ]


def _fetch_weak_knowledge_points(db, student_id: int) -> List[Dict[str, Any]]:
    """获取学生的薄弱知识点"""
    # 查询错题记录
    wrong_questions = db.query(WrongQuestion).filter(
        WrongQuestion.user_id == student_id
    ).all()
    
    # 按小节分组
    subsection_counts = {}
    for wq in wrong_questions:
        if wq.subsection_id:
            if wq.subsection_id not in subsection_counts:
                subsection_counts[wq.subsection_id] = 0
            subsection_counts[wq.subsection_id] += 1
    
    # 获取小节信息
    weak_points = []
    for sub_id, count in subsection_counts.items():
        sub = db.query(SubSection).filter(SubSection.id == sub_id).first()
        if sub:
            weak_points.append({
                "subsection_id": sub_id,
                "subsection_title": sub.title,
                "wrong_count": count
            })
    
    # 按错题数量排序
    weak_points.sort(key=lambda x: x["wrong_count"], reverse=True)
    return weak_points


async def main():
    """
    启动 MCP Server
    """
    from mcp.server.stdio import stdio_server
    
    logger.info("Starting MCP Server with all tools...")
    
    async with stdio_server() as (read_stream, write_stream):
        await server.run(
            read_stream,
            write_stream,
            server.create_initialization_options()
        )


if __name__ == "__main__":
    asyncio.run(main())
