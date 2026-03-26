"""
练习相关API路由
"""

from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.schemas.quiz import (
    QuizCreate,
    QuizCreateTargeted,
    WordTrainingCreate,
    ComprehensiveQuizCreate,
    QuizSubmit,
    QuizResponse,
    QuizResult,
    SubsectionStats,
    SectionStats
)
from app.schemas.wrong_question import KnowledgePointsResponse
from app.models.user import User
from app.models.quiz import QuizRecord
from app.models.subsection import SubSection
from app.models.section import Section
from app.models.chapter import Chapter
from app.models.knowledge_point import KnowledgePoint
from app.models.user_knowledge_stats import UserKnowledgePointStats
from sqlalchemy import func
from app.api.dependencies import get_db, get_current_active_user
from app.services.quiz_service import quiz_service
from app.services.word_training_service import word_training_service
from app.services.comprehensive_quiz_service import comprehensive_quiz_service
import json

router = APIRouter(prefix="/quiz", tags=["练习"])

# 辅助函数
def _process_single_question(content_json: dict, item: dict) -> dict:
    """处理单个题目内容"""
    import re
    
    # Normalize keys
    q_text = content_json.get("question") or content_json.get("question_text")
    raw_options = content_json.get("options")
    answer = content_json.get("answer") or content_json.get("correct_answer")
    
    # Process options to ensure Dict format {"A": "val", "B": "val"} and clean content
    final_options = None
    
    if isinstance(raw_options, list) and raw_options:
        final_options = {}
        for idx, opt in enumerate(raw_options):
            key = chr(65 + idx) # 0->A, 1->B
            # Remove prefixes like "A.", "A ", "A、"
            clean_opt = re.sub(r'^[A-D][\.\s\、]+', '', str(opt)).strip()
            final_options[key] = clean_opt
    elif isinstance(raw_options, dict) and raw_options:
        final_options = {}
        for k, v in raw_options.items():
            # Clean values as well just in case
            clean_opt = re.sub(r'^[A-D][\.\s\、]+', '', str(v)).strip()
            final_options[k] = clean_opt
    
    # Normalize answer: If it's text and matches one of the options, convert to Key (A/B/C/D)
    # Only for choice questions
    final_answer = answer
    if final_options and isinstance(answer, str):
        # Check if answer is already a key
        if answer in final_options:
            final_answer = answer
        else:
            # Check if answer matches any option value
            for k, v in final_options.items():
                if v.strip() == answer.strip():
                    final_answer = k
                    break
    
    # Determine quiz_type: Priority order: 
    # 1. AI returned 'quiz_type' field (from system instruction)
    # 2. Template type hint from service (detected from prompt text)
    # 3. Fallback: 'choice' if options exist, else 'blank'
    ai_quiz_type = content_json.get("quiz_type")
    template_type = item.get("template_type")
    
    final_quiz_type = "blank"
    if ai_quiz_type and ai_quiz_type in ["choice", "blank"]:
        final_quiz_type = ai_quiz_type
    elif template_type:
        final_quiz_type = template_type
    else:
        final_quiz_type = "choice" if final_options else "blank"

    return {
        "question_text": q_text,
        "quiz_type": final_quiz_type,
        "options": final_options if final_options else [],
        "correct_answer": final_answer,
        "explanation": "",
        "meta": {
            "word": item.get("word", "unknown"),
            "prompt": item.get("prompt", "")
        }
    }

def _create_fallback_question(item: dict) -> dict:
    """创建降级题目（当解析失败时）"""
    return {
        "question_text": "题目解析失败，请稍后重试",
        "quiz_type": "blank",
        "options": [],
        "correct_answer": "",
        "explanation": "题目生成失败，请重试",
        "meta": {
            "word": item.get("word", "unknown"),
            "prompt": item.get("prompt", "")
        }
    }

@router.post("/comprehensive/generate", response_model=QuizResponse, status_code=status.HTTP_201_CREATED)
async def generate_comprehensive_quiz(
    data: ComprehensiveQuizCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """
    生成综合训练题目 (指定节、难度、数量)
    """
    # 1. Generate questions
    result = await comprehensive_quiz_service.generate_quiz(
        db, data.section_id, data.difficulty, data.count
    )
    
    if "error" in result:
        raise HTTPException(status_code=400, detail=result["error"])
        
    questions = result["questions"]
    if not questions:
        raise HTTPException(status_code=400, detail="生成题目失败，未能生成有效题目")
    
    # 2. Get chapter info
    section = db.query(Section).filter(Section.id == data.section_id).first()
    chapter_id = section.chapter_id if section else None
    
    # 3. Create QuizRecord
    # practice_mode="random" maps to "综合训练" in frontend
    new_quiz = QuizRecord(
        user_id=current_user.id,
        chapter_id=chapter_id,
        section_id=data.section_id, # Save section_id
        practice_mode="random", 
        quiz_type="mixed",
        question_count=len(questions),
        questions=json.dumps(questions, ensure_ascii=False),
        difficulty=data.difficulty,
        score=0,
        accuracy=0,
        is_completed=0
    )
    
    db.add(new_quiz)
    db.commit()
    db.refresh(new_quiz)
    
    return new_quiz


@router.post("/word_training/generate", response_model=QuizResponse, status_code=status.HTTP_201_CREATED)
async def generate_word_training(
    data: WordTrainingCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """
    生成单词章节训练
    
    - **subsection_id**: 小目标ID
    - **count**: 题目数量
    """
    # 1. Generate questions
    generated_items = await word_training_service.generate_word_quiz(
        db, current_user.id, data.subsection_id, data.count, data.practice_mode
    )
    
    # 2. Convert to QuizRecord format
    questions_data = []
    
    for item in generated_items:
        try:
            # Check if this is a batch generation result
            if "batch_questions" in item and item.get("word") == "grammar_batch":
                # Process batch questions
                batch_questions = item["batch_questions"]
                for q_content in batch_questions:
                    questions_data.append(_process_single_question(q_content, item))
            else:
                # Process single question
                content_json = json.loads(item["question_content"])
                questions_data.append(_process_single_question(content_json, item))
        except Exception as e:
            print(f"Error parsing quiz item: {e}")
            # Fallback if JSON parsing fails
            questions_data.append(_create_fallback_question(item))
            questions_data.append({
                "question_text": item["question_content"],
                "quiz_type": "blank", # Default to blank so user can at least try to answer
                "correct_answer": "",
                "meta": {"word": item["word"], "prompt": item["prompt"]}
            })

    # 3. Create QuizRecord
    # Fetch chapter_id for better history tracking
    
    chapter_id = None
    subsection_type = "word"
    subsection = db.query(SubSection).filter(SubSection.id == data.subsection_id).first()
    if subsection:
         # Detect type
         subsection_type = word_training_service.get_subsection_type(db, subsection.id)
         
         section = db.query(Section).filter(Section.id == subsection.section_id).first()
         if section:
             chapter_id = section.chapter_id

    # Determine quiz_type for record
    # If grammar -> "grammar", else "word_training"
    record_quiz_type = "grammar" if subsection_type == "grammar" else "word_training"

    quiz_record = QuizRecord(
        user_id=current_user.id,
        quiz_type=record_quiz_type,
        practice_mode=data.practice_mode, # Use passed mode or default 'subsection'
        chapter_id=chapter_id,
        subsection_id=data.subsection_id,
        question_count=len(questions_data),
        questions=json.dumps(questions_data), # Serialize
        score=0.0,
        accuracy=0.0,
        time_spent=0
    )
    db.add(quiz_record)
    db.commit()
    db.refresh(quiz_record)
    
    # Return matched response
    return {
        **quiz_record.__dict__,
        "questions": questions_data,
        "is_completed": False
    }


@router.get("/stats/subsection/{subsection_id}", response_model=SubsectionStats)
def get_subsection_stats(
    subsection_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """
    获取指定小节的练习统计数据
    """
    # 1. Get Subsection details
    subsection = db.query(SubSection).filter(SubSection.id == subsection_id).first()
    if not subsection:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="小节不存在"
        )
        
    # 2. Get User's Quiz Records for this subsection
    # We should consider only 'subsection' practice mode or any mode?
    # Probably any quiz that targeted this subsection.
    records = db.query(QuizRecord).filter(
        QuizRecord.user_id == current_user.id,
        QuizRecord.subsection_id == subsection_id,
        QuizRecord.is_completed == 1  # Only completed quizzes count
    ).all()
    
    total_quizzes = len(records)
    total_questions = sum(r.question_count for r in records)
    
    # Calculate average score
    if total_quizzes > 0:
        # Assuming score is 0-100 based on previous code (80.0, 40.0 etc)
        # Check if score is normalized. In word training it seems to be 0-100?
        # Let's assume score in DB is the percentage score or we calculate from accuracy?
        # Looking at QuizRecord model, score is Float. In frontend table it shows 80.0.
        # Let's use the 'score' field directly.
        total_score_sum = sum(r.score for r in records)
        average_score = total_score_sum / total_quizzes
    else:
        average_score = 0.0
        
    # Assessment criteria
    weight = subsection.weight if subsection.weight is not None else 0.0
    passing_score = subsection.passing_score if subsection.passing_score is not None else 60.0
    min_questions = subsection.min_questions if subsection.min_questions is not None else 10
    
    # Final score = Average Score * (Weight / 100)
    # If weight is e.g. 20 (%), final score max is 20.
    # If total_questions < min_questions, final_score is 0.
    if total_questions < min_questions:
        final_score = 0.0
    else:
        final_score = average_score * (weight / 100.0)
    
    # Passed quizzes (score >= passing_score)
    passed_quizzes = len([r for r in records if r.score >= passing_score])
    
    return {
        "subsection_id": subsection.id,
        "subsection_title": subsection.title,
        "weight": weight,
        "passing_score": passing_score,
        "min_questions": min_questions,
        "total_quizzes": total_quizzes,
        "total_questions": total_questions,
        "average_score": round(average_score, 1),
        "final_score": round(final_score, 1),
        "passed_quizzes": passed_quizzes
    }


@router.get("/stats/section/{section_id}", response_model=SectionStats)
def get_section_stats(
    section_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """
    获取指定节的练习统计数据
    """
    # 1. Get Section details
    section = db.query(Section).filter(Section.id == section_id).first()
    if not section:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="节不存在"
        )
        
    # 2. Get User's Quiz Records for this section
    records = db.query(QuizRecord).filter(
        QuizRecord.user_id == current_user.id,
        QuizRecord.section_id == section_id,
        QuizRecord.is_completed == 1
    ).all()
    
    total_quizzes = len(records)
    total_questions = sum(r.question_count for r in records)
    
    # Calculate average score and accuracy
    average_score = 0.0
    avg_accuracy = 0.0
    max_score = 0.0
    if total_quizzes > 0:
        total_score_sum = sum(r.score for r in records)
        average_score = total_score_sum / total_quizzes
        max_score = max(r.score for r in records)
        
        # Ensure accuracy is calculated correctly
        total_accuracy_sum = sum(r.accuracy for r in records)
        avg_accuracy = total_accuracy_sum / total_quizzes
        
    # Passed quizzes (score >= 60)
    passed_quizzes = len([r for r in records if r.score >= 60.0])
    
    return {
        "section_id": section.id,
        "section_title": section.title,
        "total_quizzes": total_quizzes,
        "total_questions": total_questions,
        "average_score": round(average_score, 1),
        "avg_accuracy": round(avg_accuracy, 1),
        "max_score": round(max_score, 1),
        "passed_quizzes": passed_quizzes
    }


@router.post("/create", response_model=QuizResponse, status_code=status.HTTP_201_CREATED)
async def create_quiz(
    quiz_data: QuizCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """
    创建练习

    - **practice_mode**: 练习方式 (chapter=章节练习, random=随机练习, comprehensive=综合练习)
    - **chapter_id**: 章节ID（章节练习时必填）
    - **quiz_type**: 练习类型 (reading/translation/writing等)
    - **question_count**: 题目数量（1-20，默认5）
    """
    quiz_record = await quiz_service.create_quiz(
        db=db,
        user_id=current_user.id,
        quiz_type=quiz_data.quiz_type,
        question_count=quiz_data.question_count,
        practice_mode=quiz_data.practice_mode,
        chapter_id=quiz_data.chapter_id,
        subsection_id=quiz_data.subsection_id,
        difficulty=quiz_data.difficulty
    )

    # 创建响应字典，包含source_documents信息
    response = {
        **quiz_record.__dict__,
        "source_documents": getattr(quiz_record, 'source_documents', []),
        "source_chunks": getattr(quiz_record, 'source_chunks', []),
        "rag_context": getattr(quiz_record, 'rag_context', ""),
        "applied_rules": getattr(quiz_record, 'applied_rules', None)
    }

    return response


@router.post("/submit", response_model=QuizResult)
def submit_quiz(
    submit_data: QuizSubmit,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """
    提交练习答案

    - **quiz_id**: 练习ID
    - **user_answers**: 用户答案列表
    """
    result = quiz_service.submit_quiz(
        db=db,
        quiz_id=submit_data.quiz_id,
        user_id=current_user.id,
        user_answers=submit_data.user_answers,
        time_spent=submit_data.time_spent
    )

    return result


@router.get("/history", response_model=List[QuizResponse])
def get_quiz_history(
    practice_mode: Optional[str] = None,
    chapter_id: Optional[int] = None,
    section_id: Optional[int] = None,
    subsection_id: Optional[int] = None,
    limit: int = 10,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """
    获取练习历史

    - **practice_mode**: 按练习方式过滤（可选：chapter/random/comprehensive）
    - **chapter_id**: 按章节过滤（可选）
    - **section_id**: 按节过滤（可选）
    - **subsection_id**: 按小节过滤（可选）
    - **limit**: 返回数量限制（默认10）
    """
    records = quiz_service.get_quiz_history(
        db=db,
        user_id=current_user.id,
        practice_mode=practice_mode,
        chapter_id=chapter_id,
        section_id=section_id,
        subsection_id=subsection_id,
        limit=limit
    )

    return records


@router.get("/stats")
def get_quiz_stats(
    chapter_id: Optional[int] = None,
    practice_mode: Optional[str] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """
    获取练习统计

    - **chapter_id**: 章节ID（可选），若提供则只返回该章节的统计数据
    - **practice_mode**: 练习方式（可选）

    返回:
    - **total_count**: 总练习数
    - **completed_count**: 已完成数
    - **avg_score**: 平均分数
    - **avg_accuracy**: 平均正确率
    """
    stats = quiz_service.get_quiz_stats(db=db, user_id=current_user.id, chapter_id=chapter_id, practice_mode=practice_mode)
    return stats


@router.get("/{quiz_id}", response_model=QuizResponse)
def get_quiz(
    quiz_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """
    获取练习详情
    """
    from app.models.quiz import QuizRecord

    quiz = db.query(QuizRecord).filter(
        QuizRecord.id == quiz_id,
        QuizRecord.user_id == current_user.id
    ).first()

    if not quiz:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="练习不存在"
        )

    return quiz


@router.post("/create-targeted", response_model=QuizResponse, status_code=status.HTTP_201_CREATED)
async def create_targeted_quiz(
    quiz_data: QuizCreateTargeted,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """
    创建针对性练习（指定知识点）

    - **chapter_id**: 章节ID
    - **quiz_type**: 练习类型 (choice/blank/translation/matching/ordering/short_answer)
    - **question_count**: 题目数量（1-20，默认5）
    - **knowledge_point_ids**: 知识点ID列表（可选）

    针对指定的知识点生成题目
    """
    quiz_record = await quiz_service.create_quiz(
        db=db,
        user_id=current_user.id,
        chapter_id=quiz_data.chapter_id,
        quiz_type=quiz_data.quiz_type,
        question_count=quiz_data.question_count,
        knowledge_point_ids=quiz_data.knowledge_point_ids
    )

    return quiz_record


@router.post("/create-personalized", response_model=QuizResponse, status_code=status.HTTP_201_CREATED)
async def create_personalized_quiz(
    quiz_data: QuizCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """
    创建个性化练习

    - **chapter_id**: 章节ID
    - **quiz_type**: 练习类型 (choice/blank/translation/matching/ordering/short_answer)
    - **question_count**: 题目数量（1-20，默认5）

    基于用户的薄弱知识点自动生成针对性题目
    如果没有薄弱点数据，则创建普通练习
    """
    quiz_record = await quiz_service.create_personalized_quiz(
        db=db,
        user_id=current_user.id,
        chapter_id=quiz_data.chapter_id,
        quiz_type=quiz_data.quiz_type,
        question_count=quiz_data.question_count
    )

    # 创建响应字典，包含source_documents信息
    response = {
        **quiz_record.__dict__,
        "source_documents": getattr(quiz_record, 'source_documents', []),
        "source_chunks": getattr(quiz_record, 'source_chunks', []),
        "rag_context": getattr(quiz_record, 'rag_context', "")
    }

    return response


@router.get("/knowledge-points/{chapter_id}", response_model=KnowledgePointsResponse)
def get_knowledge_points(
    chapter_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """
    获取章节的知识点列表

    返回该章节所有文档中提取的知识点
    """
    from app.models.document import CourseDocument
    import json

    documents = db.query(CourseDocument).filter(
        CourseDocument.chapter_id == chapter_id,
        CourseDocument.knowledge_points.isnot(None)
    ).all()

    all_points = []
    for doc in documents:
        if doc.knowledge_points:
            try:
                points = json.loads(doc.knowledge_points)
                if isinstance(points, list):
                    all_points.extend(points)
            except json.JSONDecodeError:
                continue

    # 去重（基于id）
    unique_points = {}
    for point in all_points:
        if isinstance(point, dict) and 'id' in point:
            unique_points[point['id']] = point

    return {
        "chapter_id": chapter_id,
        "knowledge_points": list(unique_points.values())
    }

@router.get("/stats/teacher/grades", response_model=dict)
async def get_teacher_grade_stats(
    chapter_id: Optional[int] = None,
    section_id: Optional[int] = None,
    subsection_id: Optional[int] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """
    教师端：获取成绩分布统计
    """
    if current_user.role != "teacher":
        raise HTTPException(status_code=403, detail="权限不足")
    
    # Only consider completed quizzes from students
    # Group by user_id to get one record per student (average accuracy)
    query = db.query(
        QuizRecord.user_id,
        func.avg(QuizRecord.accuracy).label("avg_accuracy")
    ).join(User, QuizRecord.user_id == User.id)\
     .filter(QuizRecord.is_completed == 1)\
     .filter(User.role == "student")
    
    if subsection_id:
        query = query.filter(QuizRecord.subsection_id == subsection_id)
    elif section_id:
        query = query.filter(QuizRecord.section_id == section_id)
    elif chapter_id:
        query = query.filter(QuizRecord.chapter_id == chapter_id)
        
    student_stats = query.group_by(QuizRecord.user_id).all()
    total_students = len(student_stats)
    
    # Bucketize based on student average scores
    buckets = {
        "excellent": 0, # 90-100
        "good": 0,      # 80-89
        "fair": 0,      # 70-79
        "pass": 0,      # 60-69
        "fail": 0       # <60
    }
    
    total_score_sum = 0
    
    for _, avg_acc in student_stats:
        score = avg_acc if avg_acc is not None else 0
        total_score_sum += score
        if score >= 90:
            buckets["excellent"] += 1
        elif score >= 80:
            buckets["good"] += 1
        elif score >= 70:
            buckets["fair"] += 1
        elif score >= 60:
            buckets["pass"] += 1
        else:
            buckets["fail"] += 1
            
    avg_score = (total_score_sum / total_students) if total_students > 0 else 0
    
    return {
        "total_students": total_students,
        "avg_score": round(avg_score, 1),
        "distribution": [
            {"name": "优秀 (90-100)", "value": buckets["excellent"]},
            {"name": "良好 (80-89)", "value": buckets["good"]},
            {"name": "中等 (70-79)", "value": buckets["fair"]},
            {"name": "及格 (60-69)", "value": buckets["pass"]},
            {"name": "不及格 (<60)", "value": buckets["fail"]}
        ]
    }


@router.get("/stats/teacher/knowledge_points", response_model=List[dict])
async def get_teacher_kp_stats(
    chapter_id: Optional[int] = None,
    section_id: Optional[int] = None,
    subsection_id: Optional[int] = None,
    limit: int = 4,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """
    教师端：获取知识点薄弱项统计 (Top N with lowest accuracy)
    """
    if current_user.role != "teacher":
        raise HTTPException(status_code=403, detail="权限不足")
        
    # Aggregate stats from UserKnowledgePointStats
    # Join path: UserKnowledgePointStats -> KnowledgePoint -> SubSection -> Section -> Chapter
    
    query = db.query(
        KnowledgePoint.content,
        func.sum(UserKnowledgePointStats.total_attempts).label("total"),
        func.sum(UserKnowledgePointStats.correct_attempts).label("correct")
    ).join(UserKnowledgePointStats, UserKnowledgePointStats.knowledge_point_id == KnowledgePoint.id)\
     .join(SubSection, KnowledgePoint.subsection_id == SubSection.id)\
     .join(Section, SubSection.section_id == Section.id)\
     .join(Chapter, Section.chapter_id == Chapter.id)
     
    if subsection_id:
        query = query.filter(SubSection.id == subsection_id)
    elif section_id:
        query = query.filter(Section.id == section_id)
    elif chapter_id:
        query = query.filter(Chapter.id == chapter_id)
        
    stats = query.group_by(KnowledgePoint.id, KnowledgePoint.content)\
                 .having(func.sum(UserKnowledgePointStats.total_attempts) > 0)\
                 .all()
                 
    # Calculate accuracy and sort
    results = []
    for content, total, correct in stats:
        accuracy = (correct / total * 100) if total > 0 else 0
        results.append({
            "content": content,
            "accuracy": round(accuracy, 1),
            "total_attempts": total
        })
        
    # Sort by accuracy ascending (lowest first)
    results.sort(key=lambda x: x["accuracy"])
    
    return results[:limit]