"""
MCP Server for Student Learning Analytics

提供学生学情数据查询工具，供 AI 进行薄弱点分析和针对性出题

核心功能：
1. fetch_learning_data - 获取学生练习记录
2. fetch_wrong_questions - 获取错题记录
3. fetch_weak_knowledge_points - 获取薄弱知识点统计
"""

import asyncio
import json
import logging
from typing import Any, Dict, List, Optional
from datetime import datetime
import pymysql
from pymysql.cursors import DictCursor

from mcp.server import Server
from mcp.types import Tool, TextContent
from pydantic import BaseModel, Field

from config import settings

# 配置日志
logging.basicConfig(
    level=getattr(logging, settings.LOG_LEVEL),
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# 创建 MCP Server 实例
app = Server(settings.SERVER_NAME)


class DatabaseConnection:
    """数据库连接管理器"""

    def __init__(self):
        self.connection = None

    def connect(self):
        """建立数据库连接"""
        try:
            # 解析数据库 URL
            # format: mysql+pymysql://user:password@host:port/database
            url = settings.DATABASE_URL
            url = url.replace("mysql+pymysql://", "")
            parts = url.split("@")
            user_pass = parts[0].split(":")
            host_db = parts[1].split("/")
            host_port = host_db[0].split(":")

            self.connection = pymysql.connect(
                host=host_port[0],
                port=int(host_port[1]) if len(host_port) > 1 else 3306,
                user=user_pass[0],
                password=user_pass[1],
                database=host_db[1],
                charset='utf8mb4',
                cursorclass=DictCursor
            )
            logger.info("Database connected successfully")
            return self.connection
        except Exception as e:
            logger.error(f"Database connection failed: {e}")
            raise

    def close(self):
        """关闭数据库连接"""
        if self.connection:
            self.connection.close()
            logger.info("Database connection closed")

    def execute_query(self, query: str, params: tuple = ()) -> List[Dict]:
        """执行查询并返回结果"""
        try:
            if not self.connection or not self.connection.open:
                self.connect()

            # 确保能看到其他连接提交的最新数据
            # 提交当前事务（如果有），开始新事务
            self.connection.commit()

            with self.connection.cursor() as cursor:
                cursor.execute(query, params)
                results = cursor.fetchall()
                return results
        except Exception as e:
            logger.error(f"Query execution failed: {e}")
            logger.error(f"Query: {query}")
            logger.error(f"Params: {params}")
            raise


# 全局数据库连接
db = DatabaseConnection()


# 工具参数模型
class FetchLearningDataParams(BaseModel):
    """获取学习数据的参数"""
    student_id: int = Field(description="学生用户ID")
    limit: Optional[int] = Field(default=50, description="返回记录数量限制（默认50）")
    chapter_id: Optional[int] = Field(default=None, description="章节ID，用于筛选特定章节")


class FetchWrongQuestionsParams(BaseModel):
    """获取错题的参数"""
    student_id: int = Field(description="学生用户ID")
    limit: Optional[int] = Field(default=30, description="返回记录数量限制（默认30）")
    chapter_id: Optional[int] = Field(default=None, description="章节ID，用于筛选特定章节")
    is_mastered: Optional[bool] = Field(default=None, description="是否只看未掌握的错题")


class FetchWeakKnowledgePointsParams(BaseModel):
    """获取薄弱知识点的参数"""
    student_id: int = Field(description="学生用户ID")
    top_k: Optional[int] = Field(default=5, description="返回薄弱点数量（默认5）")


# 注册工具列表
@app.list_tools()
async def list_tools() -> list[Tool]:
    """列出所有可用的工具"""
    return [
        Tool(
            name="fetch_learning_data",
            description=(
                "获取学生的历史练习记录数据，包括章节、题目类型、分数、正确率、用时等。"
                "AI可以通过这些数据分析学生的学习趋势和薄弱点。"
            ),
            inputSchema=FetchLearningDataParams.model_json_schema()
        ),
        Tool(
            name="fetch_wrong_questions",
            description=(
                "获取学生的错题记录，包括错题内容、用户答案、正确答案、得分等。"
                "AI可以用于分析学生经常出错的题型和知识点。"
            ),
            inputSchema=FetchWrongQuestionsParams.model_json_schema()
        ),
        Tool(
            name="fetch_weak_knowledge_points",
            description=(
                "获取学生的薄弱知识点统计，基于错题记录聚合分析。"
                "返回错误次数最多的知识点，用于针对性出题和复习。"
            ),
            inputSchema=FetchWeakKnowledgePointsParams.model_json_schema()
        ),
    ]


# 工具实现
@app.call_tool()
async def call_tool(name: str, arguments: dict) -> list[TextContent]:
    """调用工具"""
    try:
        if name == "fetch_learning_data":
            return await fetch_learning_data(arguments)
        elif name == "fetch_wrong_questions":
            return await fetch_wrong_questions(arguments)
        elif name == "fetch_weak_knowledge_points":
            return await fetch_weak_knowledge_points(arguments)
        else:
            raise ValueError(f"Unknown tool: {name}")
    except Exception as e:
        logger.error(f"Tool execution failed: {name}, error: {e}", exc_info=True)
        return [
            TextContent(
                type="text",
                text=f"Error: {str(e)}"
            )
        ]


async def fetch_learning_data(arguments: dict) -> list[TextContent]:
    """
    获取学生练习记录数据

    从 quiz_records 表查询原始做题记录，不进行统计计算，
    只负责将数据库数据清洗后返回给 LLM
    """
    params = FetchLearningDataParams(**arguments)

    logger.info(f"Fetching learning data for student {params.student_id}")

    # 构建查询
    query = """
        SELECT
            qr.id,
            qr.chapter_id,
            c.title as chapter_title,
            qr.practice_mode,
            qr.quiz_type,
            qr.question_count,
            qr.score,
            qr.accuracy,
            qr.time_spent,
            qr.knowledge_point_ids,
            qr.questions,
            qr.results,
            qr.is_completed,
            qr.created_at,
            qr.completed_at
        FROM quiz_records qr
        LEFT JOIN chapters c ON qr.chapter_id = c.id
        WHERE qr.user_id = %s AND qr.is_completed = 1
    """

    query_params = [params.student_id]

    # 添加章节筛选
    if params.chapter_id:
        query += " AND qr.chapter_id = %s"
        query_params.append(params.chapter_id)

    # 按时间倒序，最近的记录在前
    query += " ORDER BY qr.created_at DESC"

    # 限制数量
    if params.limit:
        query += " LIMIT %s"
        query_params.append(params.limit)

    # 执行查询
    records = db.execute_query(query, tuple(query_params))

    # 格式化数据
    formatted_records = []
    for record in records:
        # 解析知识点 IDs
        knowledge_points = []
        if record.get('knowledge_point_ids'):
            try:
                knowledge_points = json.loads(record['knowledge_point_ids'])
            except:
                pass

        # 解析题目列表
        questions = []
        if record.get('questions'):
            try:
                if isinstance(record['questions'], str):
                    questions = json.loads(record['questions'])
                else:
                    questions = record['questions']
            except Exception as e:
                logger.warning(f"Failed to parse questions for quiz {record['id']}: {e}")
                questions = []

        # 解析结果列表
        results = []
        if record.get('results'):
            try:
                if isinstance(record['results'], str):
                    results = json.loads(record['results'])
                else:
                    results = record['results']
            except Exception as e:
                logger.warning(f"Failed to parse results for quiz {record['id']}: {e}")
                results = []

        formatted_records.append({
            "quiz_id": record['id'],
            "chapter_id": record['chapter_id'],
            "chapter_title": record.get('chapter_title', ''),
            "practice_mode": record.get('practice_mode', 'chapter'),  # 添加练习方式
            "quiz_type": record['quiz_type'],
            "question_count": record['question_count'],
            "score": float(record['score']) if record['score'] else 0.0,
            "accuracy": float(record['accuracy']) if record['accuracy'] else 0.0,
            "time_spent": record['time_spent'],
            "knowledge_points": knowledge_points,
            "questions": questions,  # 🔥 新增：题目列表
            "results": results,  # 🔥 新增：结果列表
            "completed_at": record['completed_at'].isoformat() if record.get('completed_at') else None,
        })

    # 返回结果
    result_text = json.dumps({
        "student_id": params.student_id,
        "total_records": len(formatted_records),
        "records": formatted_records
    }, ensure_ascii=False, indent=2)

    logger.info(f"Retrieved {len(formatted_records)} learning records for student {params.student_id}")

    return [TextContent(type="text", text=result_text)]


async def fetch_wrong_questions(arguments: dict) -> list[TextContent]:
    """
    获取学生错题记录

    从 wrong_questions 表查询学生的错题，包括题目内容、答案等详细信息
    """
    params = FetchWrongQuestionsParams(**arguments)

    logger.info(f"Fetching wrong questions for student {params.student_id}")

    # 构建查询
    query = """
        SELECT
            wq.id,
            wq.chapter_id,
            c.title as chapter_title,
            wq.question_type,
            wq.question_data,
            wq.user_answer,
            wq.correct_answer,
            wq.score,
            wq.knowledge_point_ids,
            wq.is_mastered,
            wq.retry_count,
            wq.last_retry_score,
            wq.last_retry_at,
            wq.created_at
        FROM wrong_questions wq
        LEFT JOIN chapters c ON wq.chapter_id = c.id
        WHERE wq.user_id = %s
    """

    query_params = [params.student_id]

    # 添加章节筛选
    if params.chapter_id:
        query += " AND wq.chapter_id = %s"
        query_params.append(params.chapter_id)

    # 添加掌握状态筛选
    if params.is_mastered is not None:
        query += " AND wq.is_mastered = %s"
        query_params.append(1 if params.is_mastered else 0)

    # 按时间倒序
    query += " ORDER BY wq.created_at DESC"

    # 限制数量
    if params.limit:
        query += " LIMIT %s"
        query_params.append(params.limit)

    # 执行查询
    records = db.execute_query(query, tuple(query_params))

    # 格式化数据
    formatted_records = []
    for record in records:
        # 解析知识点 IDs
        knowledge_points = []
        if record.get('knowledge_point_ids'):
            try:
                knowledge_points = json.loads(record['knowledge_point_ids'])
            except:
                pass

        # 解析题目数据
        question_data = {}
        if record.get('question_data'):
            try:
                question_data = json.loads(record['question_data'])
            except:
                pass

        formatted_records.append({
            "wrong_question_id": record['id'],
            "chapter_id": record['chapter_id'],
            "chapter_title": record.get('chapter_title', ''),
            "question_type": record['question_type'],
            "question_data": question_data,
            "user_answer": record.get('user_answer'),
            "correct_answer": record.get('correct_answer'),
            "score": float(record['score']) if record['score'] else 0.0,
            "knowledge_points": knowledge_points,
            "is_mastered": bool(record['is_mastered']),
            "retry_count": record['retry_count'],
            "last_retry_score": float(record['last_retry_score']) if record.get('last_retry_score') else None,
            "created_at": record['created_at'].isoformat() if record.get('created_at') else None,
        })

    # 返回结果
    result_text = json.dumps({
        "student_id": params.student_id,
        "total_wrong_questions": len(formatted_records),
        "wrong_questions": formatted_records
    }, ensure_ascii=False, indent=2)

    logger.info(f"Retrieved {len(formatted_records)} wrong questions for student {params.student_id}")

    return [TextContent(type="text", text=result_text)]


async def fetch_weak_knowledge_points(arguments: dict) -> list[TextContent]:
    """
    获取学生薄弱知识点统计

    基于错题记录，统计各知识点的错误次数，返回错误最多的前 K 个知识点
    """
    params = FetchWeakKnowledgePointsParams(**arguments)

    logger.info(f"Fetching weak knowledge points for student {params.student_id}")

    # 查询所有未掌握的错题（排除综合训练的错题）
    query = """
        SELECT
            wq.knowledge_point_ids,
            wq.chapter_id,
            wq.question_type
        FROM wrong_questions wq
        LEFT JOIN quiz_records qr ON wq.quiz_record_id = qr.id
        WHERE wq.user_id = %s
            AND wq.is_mastered = 0
            AND (qr.quiz_type IS NULL OR qr.quiz_type != 'comprehensive')
    """

    records = db.execute_query(query, (params.student_id,))

    # 统计知识点错误次数
    knowledge_point_stats = {}

    for record in records:
        if not record.get('knowledge_point_ids'):
            continue

        try:
            kp_ids = json.loads(record['knowledge_point_ids'])
            if not isinstance(kp_ids, list):
                continue

            for kp_id in kp_ids:
                if kp_id not in knowledge_point_stats:
                    knowledge_point_stats[kp_id] = {
                        "knowledge_point_id": kp_id,
                        "error_count": 0,
                        "chapters": set(),
                        "question_types": set()
                    }

                knowledge_point_stats[kp_id]["error_count"] += 1
                if record.get('chapter_id'):
                    knowledge_point_stats[kp_id]["chapters"].add(record['chapter_id'])
                if record.get('question_type'):
                    knowledge_point_stats[kp_id]["question_types"].add(record['question_type'])

        except:
            continue

    # 转换为列表并排序
    weak_points = []
    for kp_id, stats in knowledge_point_stats.items():
        weak_points.append({
            "knowledge_point_id": kp_id,
            "error_count": stats["error_count"],
            "related_chapters": list(stats["chapters"]),
            "question_types": list(stats["question_types"])
        })

    # 按错误次数降序排序
    weak_points.sort(key=lambda x: x["error_count"], reverse=True)

    # 限制返回数量
    if params.top_k:
        weak_points = weak_points[:params.top_k]

    # 返回结果
    result_text = json.dumps({
        "student_id": params.student_id,
        "total_weak_points": len(weak_points),
        "weak_knowledge_points": weak_points
    }, ensure_ascii=False, indent=2)

    logger.info(f"Found {len(weak_points)} weak knowledge points for student {params.student_id}")

    return [TextContent(type="text", text=result_text)]


# 主函数
async def main():
    """启动 MCP Server"""
    logger.info(f"Starting MCP Server: {settings.SERVER_NAME} v{settings.SERVER_VERSION}")

    # 连接数据库
    try:
        db.connect()
    except Exception as e:
        logger.error(f"Failed to connect to database: {e}")
        return

    # 运行服务器
    from mcp.server.stdio import stdio_server

    async with stdio_server() as (read_stream, write_stream):
        logger.info("MCP Server is running on stdio")
        await app.run(
            read_stream,
            write_stream,
            app.create_initialization_options()
        )


if __name__ == "__main__":
    try:
        asyncio.run(main())
    finally:
        db.close()
