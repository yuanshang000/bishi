"""
AI 学情分析 API 路由
"""

from fastapi import APIRouter, Depends, HTTPException, Body
from sqlalchemy.orm import Session
from typing import Optional, List, Dict, Any
from pydantic import BaseModel
from datetime import datetime
import logging

from app.api.dependencies import get_current_user, get_db
from app.models.user import User
from app.services.ai_analysis_service import ai_analysis_service
from app.services.quiz_service import quiz_service
from app.services.tts_service import tts_service

logger = logging.getLogger(__name__)

router = APIRouter()


# 请求体模型
class ComprehensiveQuizRequest(BaseModel):
    weak_points: List[Dict[str, Any]]
    question_count: int = 5


@router.get("/analysis/goal-progress")
async def get_goal_progress(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    获取目标完成情况进度
    
    返回以章-节-小目标为层级的完成度数据
    """
    try:
        progress_data = await ai_analysis_service.get_goal_completion_status(
            db=db,
            student_id=current_user.id
        )
        
        return {
            "success": True,
            "data": progress_data
        }
    except Exception as e:
        logger.error(f"Failed to get goal progress: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"获取目标进度失败: {str(e)}")


@router.get("/analysis/my-learning")
async def analyze_my_learning(
    current_user: User = Depends(get_current_user)
):
    """
    AI 分析我的学习情况

    返回详细的学习分析报告，包括：
    - 整体表现统计
    - 学习趋势
    - 薄弱知识点
    - 改进建议
    """
    try:
        # 调用 AI 分析服务
        analysis = await ai_analysis_service.analyze_student_performance(current_user.id)

        # 生成可读报告
        report = ai_analysis_service.generate_analysis_report(analysis)

        return {
            "success": True,
            "report": report,
            "data": analysis
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"分析失败: {str(e)}")


@router.get("/analysis/weak-points")
async def get_my_weak_points(
    top_k: int = 5,
    current_user: User = Depends(get_current_user)
):
    """
    获取我的薄弱知识点

    返回错误次数最多的前 K 个知识点
    """
    try:
        weak_points = await ai_analysis_service.get_weak_knowledge_points(
            current_user.id,
            top_k=top_k
        )

        return {
            "success": True,
            "weak_points": weak_points["weak_knowledge_points"],
            "total": weak_points["total_weak_points"]
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取失败: {str(e)}")


@router.get("/analysis/learning-records")
async def get_my_learning_records(
    limit: int = 20,
    current_user: User = Depends(get_current_user)
):
    """
    获取我的练习记录

    返回最近的练习记录
    """
    try:
        learning_data = await ai_analysis_service.get_learning_data(
            current_user.id,
            limit=limit
        )

        return {
            "success": True,
            "records": learning_data["records"],
            "total": learning_data["total_records"]
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取失败: {str(e)}")


@router.post("/quiz/create-targeted")
async def create_targeted_quiz(
    quiz_type: str = "reading",
    chapter_id: Optional[int] = None,
    question_count: int = 5,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    创建针对性练习（题型训练）

    不依赖章节内容，纯粹训练特定题型，提高该题型的正确率
    """
    try:
        from app.models.chapter import Chapter

        # 如果没有提供章节ID，随机选一个章节（仅用于满足数据库约束）
        if not chapter_id:
            random_chapter = db.query(Chapter).first()
            if not random_chapter:
                raise HTTPException(status_code=404, detail="系统中没有章节，请先创建章节")
            chapter_id = random_chapter.id
            logger.info(f"Using random chapter {chapter_id} for quiz type training")

        # 直接创建指定题型的练习，不基于章节内容
        quiz = await quiz_service.create_quiz(
            db=db,
            user_id=current_user.id,
            chapter_id=chapter_id,
            quiz_type=quiz_type,
            question_count=question_count,
            knowledge_point_ids=None  # 不指定知识点，纯题型训练
        )

        return {
            "success": True,
            "message": f"已生成{question_count}道{quiz_type}题型训练题",
            "quiz_id": quiz.id,
            "quiz_type": quiz_type,
            "quiz": quiz.to_dict()
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Create targeted quiz error: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"创建失败: {str(e)}")


@router.post("/quiz/create-comprehensive")
async def create_comprehensive_quiz(
    request: ComprehensiveQuizRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    创建综合练习（基于薄弱点的混合题型）

    根据用户的薄弱知识点，生成包含多种题型的综合练习。
    题目会根据薄弱点的章节和题型分布来生成，针对性强化训练。
    """
    try:
        from app.models.chapter import Chapter
        from app.services.llm_service import llm_service
        from app.models.quiz import QuizRecord
        from datetime import datetime
        import json

        weak_points = request.weak_points
        question_count = request.question_count

        logger.info(f"Creating comprehensive quiz for user {current_user.id} with {len(weak_points)} weak points")

        # 分析薄弱点，确定题型分布
        quiz_type_count = {}
        chapter_ids = set()

        for weak_point in weak_points:
            # 提取题型
            kp_id = weak_point.get('knowledge_point_id', '')

            # 题型映射
            type_map = {
                '听力理解': 'listening',
                '阅读理解': 'reading',
                '翻译练习': 'translation',
                '写作练习': 'writing',
                'listening': 'listening',
                'reading': 'reading',
                'translation': 'translation',
                'writing': 'writing'
            }

            quiz_type = type_map.get(kp_id, None)
            if quiz_type:
                quiz_type_count[quiz_type] = quiz_type_count.get(quiz_type, 0) + weak_point.get('error_count', 1)

            # 收集相关章节
            for chapter_id in weak_point.get('related_chapters', []):
                chapter_ids.add(chapter_id)

        # 如果没有识别出题型，默认使用阅读理解
        if not quiz_type_count:
            quiz_type_count = {'reading': question_count}
            logger.warning("No quiz types identified from weak points, using default: reading")

        # 根据错误次数分配题目数量
        total_errors = sum(quiz_type_count.values())
        quiz_type_distribution = {}

        for quiz_type, error_count in quiz_type_count.items():
            # 按比例分配题目数量（至少1道）
            count = max(1, round((error_count / total_errors) * question_count))
            quiz_type_distribution[quiz_type] = count

        # 确保总题数等于question_count（可能因为四舍五入有差异）
        current_total = sum(quiz_type_distribution.values())
        if current_total != question_count:
            # 调整最多的那个题型的数量
            max_type = max(quiz_type_distribution, key=quiz_type_distribution.get)
            quiz_type_distribution[max_type] += (question_count - current_total)

        logger.info(f"Quiz type distribution: {quiz_type_distribution}")

        # 获取相关章节的文档内容
        context_texts = []
        if chapter_ids:
            from app.models.document import CourseDocument
            for chapter_id in list(chapter_ids)[:3]:  # 最多取3个章节
                chapter = db.query(Chapter).filter(Chapter.id == chapter_id).first()
                if chapter:
                    docs = db.query(CourseDocument).filter(CourseDocument.chapter_id == chapter_id).limit(2).all()
                    for doc in docs:
                        if doc.content:
                            context_texts.append(f"章节{chapter.chapter_number}: {doc.content[:1000]}")

        context = "\n\n".join(context_texts) if context_texts else "英语四级学习内容"

        # 为每种题型生成题目
        all_questions = []
        for quiz_type, count in quiz_type_distribution.items():
            try:
                questions = llm_service.generate_quiz(
                    context=context,
                    quiz_type=quiz_type,
                    count=count,
                    difficulty="intermediate"
                )

                # 🔥 如果是听力题，立即转换为音频
                if quiz_type == "listening":
                    logger.info(f"Converting {len(questions)} listening questions to audio...")
                    for i, q in enumerate(questions):
                        # 详细日志：检查题目结构
                        logger.info(f"Listening question {i+1} keys: {list(q.keys())}")

                        if 'audio_text' in q:
                            audio_text = q['audio_text']
                            logger.info(f"Listening question {i+1}: audio_text length = {len(audio_text)} chars")
                            logger.debug(f"Listening question {i+1}: audio_text = {audio_text[:200]}...")

                            try:
                                # 将audio_text转换为音频
                                logger.info(f"Calling TTS service for question {i+1}...")
                                audio_url = await tts_service.text_to_speech(audio_text)
                                q['audio_url'] = audio_url

                                # 将audio_text移到explanation中
                                original_explanation = q.get('explanation', '')
                                audio_text_note = f"\n\n**音频文本：**\n{audio_text}"
                                q['explanation'] = original_explanation + audio_text_note

                                logger.info(f"Listening question {i+1}: Audio generated successfully - {audio_url}")
                            except Exception as e:
                                logger.error(f"Error generating audio for listening question {i+1}: {e}", exc_info=True)
                                q['audio_url'] = None
                        else:
                            logger.warning(f"Listening question {i+1}: Missing 'audio_text' field! Question keys: {list(q.keys())}")
                            q['audio_url'] = None
                    logger.info(f"Audio conversion completed for listening questions")

                # 为每个题目添加quiz_type字段
                for q in questions:
                    q['quiz_type'] = quiz_type

                # 输出题目结构日志（仅第一题）
                if questions and len(questions) > 0:
                    logger.info(f"Sample {quiz_type} question structure: {list(questions[0].keys())}")
                    logger.debug(f"Full sample question: {questions[0]}")

                all_questions.extend(questions)
                logger.info(f"Generated {len(questions)} {quiz_type} questions")
            except Exception as e:
                logger.error(f"Failed to generate {quiz_type} questions: {e}")
                # 继续生成其他题型

        if not all_questions:
            raise HTTPException(status_code=500, detail="题目生成失败，请重试")

        # 随机选择一个章节（用于数据库约束）
        if chapter_ids:
            chapter_id = list(chapter_ids)[0]
        else:
            random_chapter = db.query(Chapter).first()
            if not random_chapter:
                raise HTTPException(status_code=404, detail="系统中没有章节，请先创建章节")
            chapter_id = random_chapter.id

        # 创建QuizRecord对象
        # 🔥 综合练习quiz_type设为"mixed"（仅作标记，不参与AI分析统计）
        # AI分析会从questions中提取每个题目的quiz_type进行统计
        quiz = QuizRecord(
            user_id=current_user.id,
            chapter_id=chapter_id,
            practice_mode="comprehensive",  # 设置练习方式为综合练习
            quiz_type="mixed",  # 混合题型标记（数据库要求非空）
            questions=json.dumps(all_questions, ensure_ascii=False),
            question_count=len(all_questions),
            is_completed=0,  # 初始状态为未完成
            started_at=datetime.utcnow(),  # 使用UTC时间
            created_at=datetime.utcnow()
        )

        db.add(quiz)
        db.commit()
        db.refresh(quiz)

        logger.info(f"Created comprehensive quiz {quiz.id} with {len(all_questions)} questions")

        return {
            "success": True,
            "message": f"已生成{len(all_questions)}道综合练习题",
            "quiz_id": quiz.id,
            "quiz": quiz.to_dict()
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Create comprehensive quiz error: {e}", exc_info=True)
        db.rollback()
        raise HTTPException(status_code=500, detail=f"创建失败: {str(e)}")
