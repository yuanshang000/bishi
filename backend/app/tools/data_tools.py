from typing import List, Dict, Any, Optional
from sqlalchemy.orm import Session
from sqlalchemy import func, desc

from app.models.wrong_question import WrongQuestion
from app.models.quiz import QuizRecord
from app.models.chapter import Chapter
from app.models.section import Section
from app.models.subsection import SubSection
from app.models.user_word_stats import UserWordStats

import json
from app.services.rag_service import rag_service

def get_student_quiz_history(db: Session, student_id: int, limit: int = 5) -> List[Dict[str, Any]]:
    """
    获取学生最近的测验历史
    
    Args:
        db: 数据库会话
        student_id: 学生ID
        limit: 限制数量
        
    Returns:
        测验历史列表
    """
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

def search_course_content(query: str, chapter_id: Optional[int] = None, top_k: int = 3) -> List[Dict[str, Any]]:
    """
    检索课程内容向量数据库
    
    Args:
        query: 搜索查询
        chapter_id: 章节ID (可选)
        top_k: 返回数量
        
    Returns:
        检索结果
    """
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

def _get_subsection_content_summary(db: Session, subsection_id: int) -> str:
    """
    获取小节的知识点概要
    """
    from app.models.subsection import SubSection
    from app.models.knowledge_point import KnowledgePoint
    
    sub = db.query(SubSection).filter(SubSection.id == subsection_id).first()
    if not sub:
        return ""
        
    content_summary = ""
    
    # 1. 优先从 SubSection.content 获取
    if sub.content and len(sub.content) > 10:
        content_summary = f"【知识点内容】\n{sub.content}"
        return content_summary
        
    # 2. 尝试查询关联的 KnowledgePoint
    kps = db.query(KnowledgePoint).filter(KnowledgePoint.subsection_id == subsection_id).all()
    if kps:
        words = [kp for kp in kps if kp.type == 'word']
        grammar = [kp for kp in kps if kp.type == 'grammar']
        others = [kp for kp in kps if kp.type not in ['word', 'grammar']]
        
        summary_parts = []
        if words:
            summary_parts.append("[知识点:单词]")
            summary_parts.extend([f"- {kp.content}" for kp in words])
        if grammar:
            summary_parts.append("\n[知识点:语法]")
            summary_parts.extend([f"- {kp.content}" for kp in grammar])
        if others:
            summary_parts.append("\n[其他知识点]")
            summary_parts.extend([f"- {kp.content}" for kp in others])
            
        if summary_parts:
            content_summary = "【知识点内容】\n" + "\n".join(summary_parts)
            return content_summary

    # 3. RAG 搜索
    try:
        # 精确搜索
        context_text, _, _ = rag_service.get_context_for_subsection(
            subsection_id=subsection_id,
            max_length=1500,
            top_k=5
        )
        
        if context_text:
            content_summary = f"【知识点内容】\n{context_text}"
            return content_summary
            
        # 模糊搜索
        search_query = f"{sub.title} 核心词汇 重点语法"
        search_res = rag_service.search(query=search_query, top_k=3) 
        
        if search_res:
            combined_content = ""
            for res in search_res:
                content = res.get('content', '')
                combined_content += content + "\n\n"
            content_summary = f"【知识点内容】\n{combined_content[:1000]}"
            return content_summary
            
    except Exception as e:
        print(f"Error fetching content summary: {e}")
        
    return content_summary

def get_student_learning_progress(db: Session, student_id: int) -> Dict[str, Any]:
    """
    获取学生当前的学习进度（基于做题历史中最靠后的章节）
    
    Args:
        db: 数据库会话
        student_id: 学生ID
        
    Returns:
        进度信息
    """
    # 逻辑更新：不使用最近一次做题时间，而是查找用户所有做题记录中，在课程结构上最靠后的一个 subsection
    
    # 1. 获取用户所有做过的 subsection_id
    passed_sub_ids = db.query(QuizRecord.subsection_id).filter(
        QuizRecord.user_id == student_id
    ).distinct().all()
    passed_sub_ids = [r[0] for r in passed_sub_ids if r[0] is not None]
    
    if not passed_sub_ids:
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
        
    # 2. 找出这些 ID 中，在课程结构上排在最后面的一个
    # 关联查询 SubSection -> Section -> Chapter 进行排序
    latest_sub = db.query(SubSection).join(Section).join(Chapter).filter(
        SubSection.id.in_(passed_sub_ids)
    ).order_by(
        Chapter.chapter_number.desc(),
        Section.order.desc(),
        SubSection.id.desc()
    ).first()
    
    if not latest_sub:
         return {"status": "unknown", "message": "无法定位当前进度"}
         
    section = db.query(Section).filter(Section.id == latest_sub.section_id).first()
    chapter = db.query(Chapter).filter(Chapter.id == section.chapter_id).first()
    
    # 获取该 subsection 的最后一次得分（作为参考）
    last_record = db.query(QuizRecord).filter(
        QuizRecord.user_id == student_id,
        QuizRecord.subsection_id == latest_sub.id
    ).order_by(desc(QuizRecord.created_at)).first()
    
    # 获取知识点概要
    content_summary = _get_subsection_content_summary(db, latest_sub.id)
    
    return {
        "status": "in_progress",
        "current_chapter": chapter.title,
        "current_chapter_id": chapter.id,
        "current_section": section.title,
        "current_subsection": latest_sub.title,
        "last_quiz_score": last_record.score if last_record else 0,
        "last_quiz_time": last_record.created_at.isoformat() if last_record else None,
        "content_summary": content_summary
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
        # 查找学生最新的进度 - 逻辑修正：
        # 不使用 QuizRecord (最近一次做题)，因为用户可能回头复习旧章节。
        # 应该找到用户所有做题记录中，subsection_id 最大的那个（假设 ID 按章节顺序递增），
        # 或者更严谨地，按照 Chapter.order -> Section.order -> SubSection.order 排序。
        # 这里为了简化且高效，我们先获取用户所有做过的 subsection_ids，然后找出逻辑上“最后”的一个。
        
        # 1. 获取用户所有做过的 subsection_id
        passed_sub_ids = db.query(QuizRecord.subsection_id).filter(
            QuizRecord.user_id == student_id
        ).distinct().all()
        passed_sub_ids = [r[0] for r in passed_sub_ids if r[0] is not None]
        
        if not passed_sub_ids:
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

        # 2. 找出这些 ID 中，在课程结构上排在最后面的一个
        # 关联查询 SubSection -> Section -> Chapter 进行排序
        latest_sub = db.query(SubSection).join(Section).join(Chapter).filter(
            SubSection.id.in_(passed_sub_ids)
        ).order_by(
            Chapter.chapter_number.desc(),
            Section.order.desc(),
            SubSection.id.desc() # 假设 SubSection 内部按 ID 排序，或者应该用 SubSection.order (如果存在)
        ).first()
        
        if latest_sub:
            current_subsection_id = latest_sub.id
        else:
            return {"error": "Could not determine latest progress."}

    if not current_subsection_id:
        return {"error": "Either current_subsection_id or student_id must be provided"}

    current_sub = db.query(SubSection).filter(SubSection.id == current_subsection_id).first()
    if not current_sub:
        return {"error": "Invalid subsection ID"}
        
    current_section = db.query(Section).filter(Section.id == current_sub.section_id).first()
    
    # 1. 尝试找同Section下的下一个SubSection
    next_sub = db.query(SubSection).filter(
        SubSection.section_id == current_section.id,
        SubSection.id > current_sub.id
    ).order_by(SubSection.id).first()
    
    if next_sub:
        section = db.query(Section).filter(Section.id == next_sub.section_id).first()
        chapter = db.query(Chapter).filter(Chapter.id == section.chapter_id).first()
        
        # 增强：查询该小节的知识点概要 (KnowledgePoint)
        content_summary = _get_subsection_content_summary(db, next_sub.id)

        return {
            "type": "subsection",
            "title": next_sub.title,
            "context": f"{chapter.title} - {section.title} - {next_sub.title}",
            "description": f"Weight: {next_sub.weight}, Passing Score: {next_sub.passing_score}",
            "content_summary": content_summary,
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
        if first_sub:
            chapter = db.query(Chapter).filter(Chapter.id == next_section.chapter_id).first()
            return {
                "type": "subsection",
                "title": first_sub.title,
                "context": f"{chapter.title} - {next_section.title} - {first_sub.title}",
                "description": "New Section Start",
                "id": first_sub.id,
                "is_new_section": True
            }
        
    # 3. 尝试找下一个Chapter
    current_chapter = db.query(Chapter).filter(Chapter.id == current_section.chapter_id).first()
    next_chapter = db.query(Chapter).filter(
        Chapter.chapter_number > current_chapter.chapter_number
    ).order_by(Chapter.chapter_number).first()
    
    if next_chapter:
        # Find first section of next chapter
        first_section = db.query(Section).filter(Section.chapter_id == next_chapter.id).order_by(Section.order).first()
        if first_section:
            first_sub = db.query(SubSection).filter(SubSection.section_id == first_section.id).order_by(SubSection.id).first()
            if first_sub:
                return {
                    "type": "subsection",
                    "title": first_sub.title,
                    "context": f"{next_chapter.title} - {first_section.title} - {first_sub.title}",
                    "description": "New Chapter Start",
                    "id": first_sub.id,
                    "is_new_chapter": True
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
        QuizRecord.user_id == student_id
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
                WrongQuestion.user_id == student_id,
                WrongQuestion.subsection_id == sub_id
            ).scalar()
            
            # 获取具体的错题详情
            wrong_details = db.query(WrongQuestion).filter(
                WrongQuestion.user_id == student_id,
                WrongQuestion.subsection_id == sub_id
            ).limit(20).all()
            
            error_types = {}
            kp_counts = {}
            
            for wq in wrong_details:
                # 统计题型错误
                q_type = wq.question_type
                error_types[q_type] = error_types.get(q_type, 0) + 1
                
                # 统计知识点错误 (基于WrongQuestion的knowledge_point_ids字段)
                if wq.knowledge_point_ids:
                    try:
                        kp_ids = wq.knowledge_point_ids
                        if isinstance(kp_ids, str):
                            kp_ids = json.loads(kp_ids)
                        
                        if isinstance(kp_ids, list):
                            for kp_id in kp_ids:
                                kp_counts[kp_id] = kp_counts.get(kp_id, 0) + 1
                    except:
                        pass
            
            # 策略：优先使用错题中统计出的知识点ID（KnowledgePoint）
            # 如果错题中没有知识点ID（可能是旧数据或简单单词题），则退回到使用 UserWordStats 表中“练习次数最少”的单词
            
            kp_names = []
            
            # 1. 尝试从错题统计中获取知识点
            if kp_counts:
                # 取出错误次数最多的前5个知识点
                top_kps = sorted(kp_counts.items(), key=lambda x: x[1], reverse=True)[:5]
                kp_ids = [k for k, v in top_kps]
                
                # 查询KnowledgePoint表获取详细信息
                from app.models.knowledge_point import KnowledgePoint
                kps = db.query(KnowledgePoint).filter(KnowledgePoint.id.in_(kp_ids)).all()
                kp_map = {kp.id: kp for kp in kps}
                
                for k_id, count in top_kps:
                    if k_id in kp_map:
                        kp = kp_map[k_id]
                        # 格式：Content (Type) - Failed N times
                        kp_names.append(f"{kp.content} ({kp.type}) - Failed {count} times")
            
            # 2. 如果没有找到关联的知识点ID，尝试查询 UserWordStats (Backup Strategy)
            # 假设 UserWordStats.count 代表“练习/掌握次数”，次数越低越需要加强
            if not kp_names:
                 low_practice_words = db.query(UserWordStats).filter(
                     UserWordStats.user_id == student_id,
                     UserWordStats.subsection_id == sub_id
                 ).order_by(UserWordStats.count).limit(5).all()
                 
                 if low_practice_words:
                     # 格式：Word (Practice Count: N)
                     kp_names = [f"{w.word} (Practice Count: {w.count})" for w in low_practice_words]
                
            # 提取 2-3 个典型错题示例
            wrong_examples = []
            for wq in wrong_details[:3]: # 取前3个
                # 解析 question_data 获取题干
                q_content = "Unknown question"
                try:
                    q_data = wq.question_data
                    if isinstance(q_data, str):
                        q_data = json.loads(q_data)
                    
                    # 尝试获取题干，不同题型字段可能不同
                    if isinstance(q_data, dict):
                        q_content = q_data.get('question') or q_data.get('title') or q_data.get('passage') or str(q_data)[:50]
                except:
                    q_content = str(wq.question_data)[:50]
                    
                wrong_examples.append({
                    "question": q_content,
                    "your_answer": wq.user_answer,
                    "correct_answer": wq.correct_answer,
                    "type": wq.question_type
                })

            suggestion = f"Recommend reviewing vocabulary and grammar for this section."
            if kp_names:
                suggestion += f" Specifically, focus on: {', '.join(kp_names)}."
            if error_types:
                top_type = max(error_types.items(), key=lambda x: x[1])[0]
                suggestion += f" You seem to struggle with {top_type} questions. Please analyze the 'recent_wrong_examples' to give specific advice."

            weak_points.append({
                "subsection_id": sub_id,
                "context": f"{chapter.title} - {section.title} - {sub.title}",
                "average_score": float(score),
                "wrong_question_count": wrong_count,
                "suggestion": suggestion,
                "specific_weaknesses": kp_names,
                "recent_wrong_examples": wrong_examples
            })
            
    return {
        "weak_points": weak_points,
        "overall_analysis": "Based on your quiz scores, these are your top 3 areas for improvement."
    }
