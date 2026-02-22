from typing import List, Dict, Any, Optional
from sqlalchemy.orm import Session
from sqlalchemy import func, desc

from app.models.wrong_question import WrongQuestion
from app.models.quiz import QuizRecord
from app.models.chapter import Chapter
from app.models.section import Section
from app.models.subsection import SubSection

def get_wrong_questions_by_subsection(db: Session, student_id: int, subsection_id: int, limit: int = 5) -> List[Dict[str, Any]]:
    """
    获取指定小目标的错题记录
    
    Args:
        db: 数据库会话
        student_id: 学生ID
        subsection_id: 小目标ID
        limit: 返回数量限制
        
    Returns:
        错题列表
    """
    wrong_questions = db.query(WrongQuestion).filter(
        WrongQuestion.student_id == student_id,
        WrongQuestion.subsection_id == subsection_id
    ).order_by(desc(WrongQuestion.error_count)).limit(limit).all()
    
    return [
        {
            "id": wq.id,
            "question_content": wq.question_content,
            "error_count": wq.error_count,
            "last_error_time": wq.updated_at.isoformat() if wq.updated_at else None
        }
        for wq in wrong_questions
    ]

def get_student_learning_progress(db: Session, student_id: int) -> Dict[str, Any]:
    """
    获取学生当前的学习进度（基于最近一次测验记录）
    
    Args:
        db: 数据库会话
        student_id: 学生ID
        
    Returns:
        进度信息
    """
    last_record = db.query(QuizRecord).filter(
        QuizRecord.student_id == student_id
    ).order_by(desc(QuizRecord.created_at)).first()
    
    if not last_record:
        # 如果没有记录，假设从第一章第一节开始
        first_chapter = db.query(Chapter).order_by(Chapter.chapter_number).first()
        if not first_chapter:
            return {"status": "no_content", "message": "暂无课程内容"}
            
        return {
            "status": "not_started",
            "current_chapter": first_chapter.title,
            "current_chapter_id": first_chapter.id,
            "message": "尚未开始学习"
        }
        
    # 获取详细信息
    subsection = db.query(SubSection).filter(SubSection.id == last_record.subsection_id).first()
    if not subsection:
         return {"status": "unknown", "message": "无法定位当前进度"}
         
    section = db.query(Section).filter(Section.id == subsection.section_id).first()
    chapter = db.query(Chapter).filter(Chapter.id == section.chapter_id).first()
    
    return {
        "status": "in_progress",
        "current_chapter": chapter.title,
        "current_chapter_id": chapter.id,
        "current_section": section.title,
        "current_subsection": subsection.title,
        "last_quiz_score": last_record.score,
        "last_quiz_time": last_record.created_at.isoformat()
    }

def get_next_content(db: Session, current_subsection_id: Optional[int] = None, student_id: Optional[int] = None) -> Dict[str, Any]:
    """
    获取下一阶段的学习内容
    
    Args:
        db: 数据库会话
        current_subsection_id: 当前完成的小目标ID (可选)
        student_id: 学生ID (可选，如果提供则自动查找最新进度)
        
    Returns:
        下一章节/小节内容信息
    """
    if student_id and not current_subsection_id:
        # 查找学生最新的进度
        last_record = db.query(QuizRecord).filter(
            QuizRecord.student_id == student_id
        ).order_by(desc(QuizRecord.created_at)).first()
        
        if last_record and last_record.subsection_id:
            current_subsection_id = last_record.subsection_id
        else:
            # 如果没有记录，返回第一章第一节
            first_chapter = db.query(Chapter).order_by(Chapter.chapter_number).first()
            if first_chapter:
                first_section = db.query(Section).filter(Section.chapter_id == first_chapter.id).order_by(Section.order).first()
                if first_section:
                    first_sub = db.query(SubSection).filter(SubSection.section_id == first_section.id).order_by(SubSection.id).first()
                    if first_sub:
                         return {
                            "type": "subsection",
                            "title": first_sub.title,
                            "description": "Start your learning journey here.",
                            "id": first_sub.id,
                            "chapter_title": first_chapter.title
                        }
            return {"message": "No content available or history found."}

    if not current_subsection_id:
        return {"error": "Either current_subsection_id or student_id must be provided"}

    current_sub = db.query(SubSection).filter(SubSection.id == current_subsection_id).first()
    if not current_sub:
        return {"error": "Invalid subsection ID"}
        
    current_section = db.query(Section).filter(Section.id == current_sub.section_id).first()
    
    # 1. 尝试找同Section下的下一个SubSection
    # 假设SubSection按ID排序，或者需要order字段。这里暂时按ID大来找
    next_sub = db.query(SubSection).filter(
        SubSection.section_id == current_section.id,
        SubSection.id > current_sub.id
    ).order_by(SubSection.id).first()
    
    if next_sub:
        return {
            "type": "subsection",
            "title": next_sub.title,
            "description": f"Weight: {next_sub.weight}, Passing Score: {next_sub.passing_score}",
            "id": next_sub.id
        }
        
    # 2. 尝试找同Chapter下的下一个Section
    next_section = db.query(Section).filter(
        Section.chapter_id == current_section.chapter_id,
        Section.order > current_section.order
    ).order_by(Section.order).first()
    
    if next_section:
        # 获取该Section的第一个SubSection
        first_sub = db.query(SubSection).filter(SubSection.section_id == next_section.id).order_by(SubSection.id).first()
        return {
            "type": "section",
            "title": next_section.title,
            "description": "New Section",
            "first_subsection_id": first_sub.id if first_sub else None
        }
        
    # 3. 尝试找下一个Chapter
    current_chapter = db.query(Chapter).filter(Chapter.id == current_section.chapter_id).first()
    next_chapter = db.query(Chapter).filter(
        Chapter.chapter_number > current_chapter.chapter_number
    ).order_by(Chapter.chapter_number).first()
    
    if next_chapter:
        return {
            "type": "chapter",
            "title": next_chapter.title,
            "description": next_chapter.description,
            "id": next_chapter.id
        }
        
    return {"type": "completed", "message": "You have completed all courses!"}

def get_student_weak_points(db: Session, student_id: int) -> Dict[str, Any]:
    """
    分析学生薄弱点
    
    Args:
        db: 数据库会话
        student_id: 学生ID
        
    Returns:
        薄弱点分析结果
    """
    # 1. 找出平均分最低的3个小目标
    weak_subsections = db.query(
        QuizRecord.subsection_id,
        func.avg(QuizRecord.score).label('avg_score')
    ).filter(
        QuizRecord.student_id == student_id
    ).group_by(
        QuizRecord.subsection_id
    ).order_by('avg_score').limit(3).all()
    
    weak_points = []
    for sub_id, score in weak_subsections:
        sub = db.query(SubSection).filter(SubSection.id == sub_id).first()
        if sub:
            section = db.query(Section).filter(Section.id == sub.section_id).first()
            chapter = db.query(Chapter).filter(Chapter.id == section.chapter_id).first()
            
            # 统计该小目标的错题数
            wrong_count = db.query(func.count(WrongQuestion.id)).filter(
                WrongQuestion.student_id == student_id,
                WrongQuestion.subsection_id == sub_id
            ).scalar()
            
            weak_points.append({
                "subsection_id": sub_id,
                "context": f"{chapter.title} - {section.title}",
                "average_score": float(score),
                "wrong_question_count": wrong_count,
                "suggestion": "Recommend reviewing vocabulary and grammar for this section."
            })
            
    return {
        "weak_points": weak_points,
        "overall_analysis": "Based on your quiz scores, these are your top 3 areas for improvement."
    }
