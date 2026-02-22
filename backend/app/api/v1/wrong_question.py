"""
错题相关API路由
"""

from typing import List, Optional, Any
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session

from app.models.user import User
from app.api.dependencies import get_db, get_current_active_user
from app.services.wrong_question_service import wrong_question_service
from app.schemas.wrong_question import (
    WrongQuestionResponse,
    WeakKnowledgePoint,
    ReviewQuizResponse,
    MasteryUpdate,
    WrongQuestionStats
)

router = APIRouter(prefix="/wrong-questions", tags=["错题管理"])


@router.get("/tree", response_model=List[dict])
def get_wrong_questions_tree(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """
    获取错题库目录树（按章节-小节结构统计）
    """
    tree = wrong_question_service.get_wrong_questions_tree(
        db=db,
        user_id=current_user.id
    )
    return tree


@router.get("/list", response_model=List[WrongQuestionResponse])
def get_wrong_questions(
    chapter_id: Optional[int] = Query(None, description="按章节过滤"),
    section_id: Optional[int] = Query(None, description="按节过滤"),
    subsection_id: Optional[int] = Query(None, description="按小节过滤"),
    is_mastered: Optional[bool] = Query(None, description="是否已掌握"),
    practice_mode: Optional[str] = Query(None, description="练习模式(chapter/random)"),
    limit: int = Query(20, ge=1, le=100, description="返回数量"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """
    获取错题列表

    可按章节、小节和掌握状态过滤
    """
    wrong_questions = wrong_question_service.get_wrong_questions(
        db=db,
        user_id=current_user.id,
        chapter_id=chapter_id,
        section_id=section_id,
        subsection_id=subsection_id,
        is_mastered=is_mastered,
        practice_mode=practice_mode,
        limit=limit
    )

    # 转换为响应格式
    result = []
    for wq in wrong_questions:
        import json
        # We need to include subsection_id in response if we want frontend to debug, but it's not in the response model explicitly shown here?
        # Actually WrongQuestionResponse might not have it. Let's assume schema matches.
        # But wait, frontend needs subsection_id for the previous filter I wrote (which I'm removing).
        # But for correctness, let's include it.
        result.append({
            "id": wq.id,
            "user_id": wq.user_id,
            "quiz_record_id": wq.quiz_record_id,
            "chapter_id": wq.chapter_id,
            "subsection_id": wq.subsection_id,
            "question_type": wq.question_type,
            "question_data": json.loads(wq.question_data) if wq.question_data else {},
            "user_answer": wq.user_answer,
            "correct_answer": wq.correct_answer,
            "score": wq.score,
            "knowledge_point_ids": json.loads(wq.knowledge_point_ids) if wq.knowledge_point_ids else [],
            "is_mastered": bool(wq.is_mastered),
            "retry_count": wq.retry_count,
            "last_retry_score": wq.last_retry_score,
            "last_retry_at": wq.last_retry_at,
            "created_at": wq.created_at
        })

    return result

@router.post("/{wrong_question_id}/generate-similar")
async def generate_similar_question(
    wrong_question_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """
    举一反三：根据错题生成相似题目
    """
    try:
        new_question = await wrong_question_service.generate_similar_question(
            db=db,
            user_id=current_user.id,
            wrong_question_id=wrong_question_id
        )
        return new_question
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"生成失败: {str(e)}"
        )



@router.get("/weak-points", response_model=List[WeakKnowledgePoint])
def get_weak_knowledge_points(
    chapter_id: Optional[int] = Query(None, description="按章节过滤"),
    top_k: int = Query(5, ge=1, le=20, description="返回前K个"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """
    获取薄弱知识点统计

    返回错误次数最多的知识点
    """
    weak_points = wrong_question_service.get_weak_knowledge_points(
        db=db,
        user_id=current_user.id,
        chapter_id=chapter_id,
        top_k=top_k
    )

    return weak_points


@router.post("/review-quiz", response_model=ReviewQuizResponse)
def create_review_quiz(
    chapter_id: Optional[int] = Query(None, description="按章节过滤"),
    question_count: int = Query(5, ge=1, le=20, description="题目数量"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """
    创建错题重练练习

    从未掌握的错题中随机选择题目
    """
    result = wrong_question_service.create_review_quiz(
        db=db,
        user_id=current_user.id,
        chapter_id=chapter_id,
        question_count=question_count
    )

    if not result['questions']:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="没有可重练的错题"
        )

    return result


@router.post("/review-quiz/submit")
def submit_review_quiz(
    wrong_question_ids: List[int],
    user_answers: List[Any],
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """
    提交错题重练答案

    自动批改，做对的题目会标记为已掌握
    """
    try:
        result = wrong_question_service.submit_review_quiz(
            db=db,
            user_id=current_user.id,
            wrong_question_ids=wrong_question_ids,
            user_answers=user_answers
        )

        return {
            "success": True,
            "message": f"批改完成！本次答对 {result['correct_count']} 题，新掌握 {result['newly_mastered_count']} 题",
            **result
        }
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"提交失败: {str(e)}"
        )


@router.patch("/{wrong_question_id}/mastery", status_code=status.HTTP_200_OK)
def update_mastery_status(
    wrong_question_id: int,
    mastery_data: MasteryUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """
    更新错题掌握状态

    通常在学生重新做对某道错题后调用
    """
    success = wrong_question_service.update_mastery_status(
        db=db,
        wrong_question_id=wrong_question_id,
        is_mastered=mastery_data.is_mastered,
        retry_score=mastery_data.retry_score
    )

    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="错题不存在"
        )

    return {"message": "更新成功"}


@router.get("/stats", response_model=WrongQuestionStats)
def get_wrong_question_stats(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """
    获取错题统计

    返回总错题数、未掌握数、已掌握数和掌握率
    """
    from app.models.wrong_question import WrongQuestion

    total_count = db.query(WrongQuestion).filter(
        WrongQuestion.user_id == current_user.id
    ).count()

    unmastered_count = db.query(WrongQuestion).filter(
        WrongQuestion.user_id == current_user.id,
        WrongQuestion.is_mastered == 0
    ).count()

    mastered_count = total_count - unmastered_count
    mastery_rate = round(mastered_count / total_count * 100, 2) if total_count > 0 else 0

    return {
        "total_count": total_count,
        "unmastered_count": unmastered_count,
        "mastered_count": mastered_count,
        "mastery_rate": mastery_rate
    }


@router.get("/{wrong_question_id}/detail")
def get_wrong_question_detail(
    wrong_question_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """
    获取错题详情

    返回完整的题目信息，包括选项、文章内容等
    """
    from app.models.wrong_question import WrongQuestion
    import json

    wrong_q = db.query(WrongQuestion).filter(
        WrongQuestion.id == wrong_question_id,
        WrongQuestion.user_id == current_user.id
    ).first()

    if not wrong_q:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="错题不存在"
        )

    # 解析题目数据
    question_data = json.loads(wrong_q.question_data) if wrong_q.question_data else {}

    return {
        "id": wrong_q.id,
        "chapter_id": wrong_q.chapter_id,
        "question_type": wrong_q.question_type,
        "question_data": question_data,  # 完整的题目数据，包括选项、文章等
        "user_answer": wrong_q.user_answer,
        "correct_answer": wrong_q.correct_answer,
        "score": wrong_q.score,
        "is_mastered": bool(wrong_q.is_mastered),
        "retry_count": wrong_q.retry_count,
        "last_retry_score": wrong_q.last_retry_score,
        "last_retry_at": wrong_q.last_retry_at,
        "created_at": wrong_q.created_at
    }


@router.get("/stats/by-chapter")
def get_wrong_question_stats_by_chapter(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """
    按章节统计错题数据

    返回每个章节的错题数量、题型分布等统计信息
    """
    from app.models.wrong_question import WrongQuestion
    from app.models.chapter import Chapter
    from sqlalchemy import func, Integer
    import json

    # 按章节统计错题数量
    chapter_stats = db.query(
        WrongQuestion.chapter_id,
        func.count(WrongQuestion.id).label('total_count'),
        func.sum(func.cast(WrongQuestion.is_mastered == 0, Integer)).label('unmastered_count')
    ).filter(
        WrongQuestion.user_id == current_user.id
    ).group_by(
        WrongQuestion.chapter_id
    ).all()

    # 获取章节信息
    chapter_ids = [stat.chapter_id for stat in chapter_stats]
    chapters = db.query(Chapter).filter(Chapter.id.in_(chapter_ids)).all()
    chapter_map = {c.id: c for c in chapters}

    # 按题型统计
    type_stats = db.query(
        WrongQuestion.chapter_id,
        WrongQuestion.question_type,
        func.count(WrongQuestion.id).label('count')
    ).filter(
        WrongQuestion.user_id == current_user.id
    ).group_by(
        WrongQuestion.chapter_id,
        WrongQuestion.question_type
    ).all()

    # 组织数据
    result = []
    for stat in chapter_stats:
        chapter = chapter_map.get(stat.chapter_id)
        if not chapter:
            continue

        # 该章节的题型分布
        type_distribution = {}
        for type_stat in type_stats:
            if type_stat.chapter_id == stat.chapter_id:
                type_distribution[type_stat.question_type] = type_stat.count

        result.append({
            "chapter_id": stat.chapter_id,
            "chapter_number": chapter.chapter_number,
            "chapter_title": chapter.title,
            "total_count": stat.total_count,
            "unmastered_count": stat.unmastered_count or 0,
            "mastered_count": stat.total_count - (stat.unmastered_count or 0),
            "type_distribution": type_distribution
        })

    # 按章节号排序
    result.sort(key=lambda x: x['chapter_number'])

    return {
        "total_chapters": len(result),
        "chapter_stats": result
    }
