"""
数据访问层 - 学生学情数据查询工具

【重要说明】
本模块是一个纯粹的数据访问层（Data Access Layer），通过 Tool Calling 方式提供数据查询功能。

【架构说明】
- 不是 MCP Server（Model Context Protocol Server）
- 不是独立运行的服务进程
- 是一个 Python 模块，提供数据查询函数
- 被 ai_analysis_service.py 直接导入和调用

【核心功能】
1. fetch_learning_data - 获取学生练习记录
2. fetch_wrong_questions - 获取错题记录
3. fetch_weak_knowledge_points - 获取薄弱知识点统计

【设计理念】
- 只负责数据搬运，不做业务逻辑
- 返回原始数据，让调用方（AI分析服务）进行深度分析
- 支持灵活筛选（按章节、时间、掌握状态等）
- 格式化输出为易于理解的 JSON 格式
"""

import json
import logging
from typing import Any, Dict, List, Optional
from datetime import datetime
import pymysql
from pymysql.cursors import DictCursor
from pydantic import BaseModel, Field

from config import settings

# 配置日志
logging.basicConfig(
    level=getattr(logging, settings.LOG_LEVEL),
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class DatabaseConnection:
    """
    数据库连接管理器
    
    负责管理 MySQL 数据库连接，提供查询执行功能
    """

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
        """
        执行查询并返回结果
        
        Args:
            query: SQL 查询语句
            params: 查询参数
            
        Returns:
            查询结果列表
        """
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


# 全局数据库连接实例
db = DatabaseConnection()


# ==================== 参数模型定义 ====================

class FetchLearningDataParams(BaseModel):
    """获取学习数据的参数模型"""
    student_id: int = Field(description="学生用户ID")
    limit: Optional[int] = Field(default=50, description="返回记录数量限制（默认50）")
    chapter_id: Optional[int] = Field(default=None, description="章节ID，用于筛选特定章节")


class FetchWrongQuestionsParams(BaseModel):
    """获取错题的参数模型"""
    student_id: int = Field(description="学生用户ID")
    limit: Optional[int] = Field(default=30, description="返回记录数量限制（默认30）")
    chapter_id: Optional[int] = Field(default=None, description="章节ID，用于筛选特定章节")
    is_mastered: Optional[bool] = Field(default=None, description="是否只看未掌握的错题")


class FetchWeakKnowledgePointsParams(BaseModel):
    """获取薄弱知识点的参数模型"""
    student_id: int = Field(description="学生用户ID")
    top_k: Optional[int] = Field(default=5, description="返回薄弱点数量（默认5）")


# ==================== 数据查询函数 ====================

async def fetch_learning_data(arguments: dict) -> List[Dict[str, Any]]:
    """
    获取学生练习记录数据
    
    【功能说明】
    从 quiz_records 表查询学生的历史练习记录，包括章节、题型、分数、正确率等。
    返回原始数据，不进行统计计算，由调用方进行深度分析。
    
    【参数说明】
    - student_id: 学生用户ID（必填）
    - limit: 返回记录数量限制（默认50）
    - chapter_id: 章节ID筛选（可选）
    
    【返回数据结构】
    {
        "student_id": 1,
        "total_records": 10,
        "records": [
            {
                "quiz_id": 10,
                "chapter_id": 2,
                "chapter_title": "情态动词",
                "practice_mode": "chapter",
                "quiz_type": "reading",
                "question_count": 5,
                "score": 45.0,
                "accuracy": 40.0,
                "time_spent": 180,
                "knowledge_points": ["modal_verbs", "grammar"],
                "questions": [...],  # 题目列表
                "results": [...],    # 答题结果
                "completed_at": "2024-05-03T10:30:00"
            }
        ]
    }
    """
    params = FetchLearningDataParams(**arguments)
    
    logger.info(f"[Tool Calling] fetch_learning_data - student_id={params.student_id}, limit={params.limit}, chapter_id={params.chapter_id}")

    # 构建 SQL 查询
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
            "practice_mode": record.get('practice_mode', 'chapter'),
            "quiz_type": record['quiz_type'],
            "question_count": record['question_count'],
            "score": float(record['score']) if record['score'] else 0.0,
            "accuracy": float(record['accuracy']) if record['accuracy'] else 0.0,
            "time_spent": record['time_spent'],
            "knowledge_points": knowledge_points,
            "questions": questions,
            "results": results,
            "completed_at": record['completed_at'].isoformat() if record.get('completed_at') else None,
        })

    # 返回结果
    result = {
        "student_id": params.student_id,
        "total_records": len(formatted_records),
        "records": formatted_records
    }

    logger.info(f"[Tool Calling] fetch_learning_data completed - retrieved {len(formatted_records)} records")

    return result


async def fetch_wrong_questions(arguments: dict) -> List[Dict[str, Any]]:
    """
    获取学生错题记录
    
    【功能说明】
    从 wrong_questions 表查询学生的错题记录，包括题目内容、用户答案、正确答案等详细信息。
    
    【参数说明】
    - student_id: 学生用户ID（必填）
    - limit: 返回记录数量限制（默认30）
    - chapter_id: 章节ID筛选（可选）
    - is_mastered: 是否只看未掌握的错题（可选）
    
    【返回数据结构】
    {
        "student_id": 1,
        "total_wrong_questions": 5,
        "wrong_questions": [
            {
                "wrong_question_id": 10,
                "chapter_id": 2,
                "chapter_title": "情态动词",
                "question_type": "reading",
                "question_data": {...},
                "user_answer": "A",
                "correct_answer": "B",
                "score": 0.0,
                "knowledge_points": ["modal_verbs"],
                "is_mastered": false,
                "retry_count": 2,
                "last_retry_score": 0.0,
                "created_at": "2024-05-03T10:30:00"
            }
        ]
    }
    """
    params = FetchWrongQuestionsParams(**arguments)
    
    logger.info(f"[Tool Calling] fetch_wrong_questions - student_id={params.student_id}, limit={params.limit}, chapter_id={params.chapter_id}, is_mastered={params.is_mastered}")

    # 构建 SQL 查询
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
    result = {
        "student_id": params.student_id,
        "total_wrong_questions": len(formatted_records),
        "wrong_questions": formatted_records
    }

    logger.info(f"[Tool Calling] fetch_wrong_questions completed - retrieved {len(formatted_records)} wrong questions")

    return result


async def fetch_weak_knowledge_points(arguments: dict) -> List[Dict[str, Any]]:
    """
    获取学生薄弱知识点统计
    
    【功能说明】
    基于错题记录，统计各知识点的错误次数，返回错误最多的前 K 个知识点。
    
    【参数说明】
    - student_id: 学生用户ID（必填）
    - top_k: 返回薄弱点数量（默认5）
    
    【返回数据结构】
    {
        "student_id": 1,
        "total_weak_points": 3,
        "weak_knowledge_points": [
            {
                "knowledge_point_id": "modal_verbs",
                "error_count": 8,
                "related_chapters": [2, 3],
                "question_types": ["reading", "translation"]
            }
        ]
    }
    """
    params = FetchWeakKnowledgePointsParams(**arguments)
    
    logger.info(f"[Tool Calling] fetch_weak_knowledge_points - student_id={params.student_id}, top_k={params.top_k}")

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
    result = {
        "student_id": params.student_id,
        "total_weak_points": len(weak_points),
        "weak_knowledge_points": weak_points
    }

    logger.info(f"[Tool Calling] fetch_weak_knowledge_points completed - found {len(weak_points)} weak points")

    return result
