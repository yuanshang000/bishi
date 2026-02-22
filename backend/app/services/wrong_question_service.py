"""
错题服务

提供错题记录、查询、统计和重练功能
"""

from typing import List, Dict, Any, Optional
from sqlalchemy.orm import Session
from sqlalchemy import func
from datetime import datetime
import json
import logging

from app.models.wrong_question import WrongQuestion
from app.models.quiz import QuizRecord

logger = logging.getLogger(__name__)


class WrongQuestionService:
    """错题服务类"""

    @staticmethod
    def record_wrong_questions(
        db: Session,
        quiz_record: QuizRecord,
        wrong_results: List[Dict[str, Any]]
    ) -> int:
        """
        记录错题

        Args:
            db: 数据库会话
            quiz_record: 练习记录
            wrong_results: 错误题目列表

        Returns:
            int: 记录的错题数量
        """
        questions = json.loads(quiz_record.questions) if quiz_record.questions else []

        count = 0
        for wrong in wrong_results:
            idx = wrong.get('question_index')
            if idx is None or idx >= len(questions):
                continue

            question_data = questions[idx]

            wrong_q = WrongQuestion(
                user_id=quiz_record.user_id,
                quiz_record_id=quiz_record.id,
                chapter_id=quiz_record.chapter_id,
                section_id=quiz_record.section_id, # Copy section_id
                subsection_id=quiz_record.subsection_id,  # Add subsection_id
                question_type=quiz_record.quiz_type,
                question_data=json.dumps(question_data, ensure_ascii=False),
                user_answer=json.dumps(wrong.get('user_answer'), ensure_ascii=False),
                correct_answer=json.dumps(wrong.get('correct_answer'), ensure_ascii=False),
                score=wrong.get('score', 0),
                knowledge_point_ids=quiz_record.knowledge_point_ids,  # 继承练习的知识点
            )

            db.add(wrong_q)
            count += 1

        if count > 0:
            db.commit()
            logger.info(f"Recorded {count} wrong questions for quiz {quiz_record.id}")

        return count

    @staticmethod
    def get_wrong_questions_tree(
        db: Session,
        user_id: int
    ) -> List[Dict[str, Any]]:
        """
        获取错题库目录树（按章节-小节结构统计）
        """
        from app.models.chapter import Chapter
        from app.models.section import Section
        from app.models.subsection import SubSection
        from sqlalchemy import func
        
        logger.info(f"Fetching wrong questions tree for user_id: {user_id}")

        # 1. 统计每个 subsection 的错题数
        # (subsection_id, count)
        sub_stats = db.query(
            WrongQuestion.subsection_id,
            func.count(WrongQuestion.id).label('count')
        ).filter(
            WrongQuestion.user_id == user_id,
            WrongQuestion.subsection_id.isnot(None)
        ).group_by(
            WrongQuestion.subsection_id
        ).all()
        
        sub_count_map = {s[0]: s[1] for s in sub_stats if s[0] is not None}
        logger.info(f"Sub stats: {sub_count_map}")
        
        # 2. 统计每个 section 的错题数 (仅包括没有subsection_id的综合训练题目)
        # 注意：这里我们只统计直接关联到section但没有subsection的题目（即综合训练题目）
        section_stats = db.query(
            WrongQuestion.section_id,
            func.count(WrongQuestion.id).label('count')
        ).filter(
            WrongQuestion.user_id == user_id,
            WrongQuestion.section_id.isnot(None),
            WrongQuestion.subsection_id.is_(None)
        ).group_by(
            WrongQuestion.section_id
        ).all()
        
        section_direct_count_map = {s[0]: s[1] for s in section_stats if s[0] is not None}
        logger.info(f"Section direct stats: {section_direct_count_map}")

        # 3. 统计每个 chapter 的错题数
        chapter_stats = db.query(
             WrongQuestion.chapter_id,
             func.count(WrongQuestion.id).label('count')
        ).filter(
            WrongQuestion.user_id == user_id
        ).group_by(
            WrongQuestion.chapter_id
        ).all()
        chapter_count_map = {c[0]: c[1] for c in chapter_stats}
        logger.info(f"Chapter stats: {chapter_count_map}")

        # 4. 构建完整树结构
        chapters = db.query(Chapter).order_by(Chapter.chapter_number).all()
        
        tree = []
        for chapter in chapters:
            chapter_count = chapter_count_map.get(chapter.id, 0)
            
            # Sections
            sections = db.query(Section).filter(Section.chapter_id == chapter.id).order_by(Section.order).all()
            section_nodes = []
            
            for section in sections:
                # Subsections
                subsections = db.query(SubSection).filter(SubSection.section_id == section.id).order_by(SubSection.order).all()
                sub_nodes = []
                section_sub_total = 0
                
                for sub in subsections:
                    count = sub_count_map.get(sub.id, 0)
                    # Always include subsection even if count is 0
                    sub_nodes.append({
                        "id": sub.id,
                        "label": f"{sub.title}",
                        "type": "subsection",
                        "count": count
                    })
                    section_sub_total += count
                
                # section_count = sum of subsections + direct comprehensive questions
                direct_count = section_direct_count_map.get(section.id, 0)
                section_total = section_sub_total + direct_count
                
                # Always include section even if total is 0
                section_nodes.append({
                    "id": section.id,
                    "label": f"{section.title}",
                    "type": "section",
                    "count": section_total,
                    "children": sub_nodes,
                    "direct_count": direct_count # Optional: info about direct questions
                })
            
            # Always add chapter even if count is 0
            tree.append({
                "id": chapter.id,
                "label": f"{chapter.title}",
                "type": "chapter",
                "count": chapter_count,
                "children": section_nodes
            })
                
        return tree

    @staticmethod
    async def generate_similar_question(
        db: Session,
        user_id: int,
        wrong_question_id: int
    ) -> Dict[str, Any]:
        """
        举一反三：根据错题生成相似题目
        """
        from app.services.word_training_service import word_training_service
        
        wq = db.query(WrongQuestion).filter(
            WrongQuestion.id == wrong_question_id,
            WrongQuestion.user_id == user_id
        ).first()
        
        if not wq:
            raise ValueError("Wrong question not found")
            
        try:
            q_data = json.loads(wq.question_data)
        except:
            raise ValueError("Invalid question data")
            
        meta = q_data.get("meta", {})
        word = meta.get("word")
        # prompt = meta.get("prompt") # prompt is actually the full text, we might want to re-use templates
        
        if not word:
             raise ValueError("Cannot generate similar question: Missing target word/knowledge in original question.")
             
        # Detect type from wq.question_type or subsection
        # If wq.question_type is 'grammar', use grammar templates.
        # If 'word_training', use word templates.
        
        type_tag = "单词"
        if wq.question_type == "grammar":
            type_tag = "语法"
        
        # Load templates
        templates = word_training_service.load_prompt_templates(type_tag)
        if not templates:
             raise ValueError(f"No templates found for type {type_tag}")
             
        import random
        template = random.choice(templates)
        
        # Generate
        # Note: word_training_service.generate_single_question is async
        # We need to await it. This method must be async.
        
        # For grammar, 'word' might be the core grammar content.
        # In word_training_service, for grammar, it constructs content like "Core\nUsage".
        # The 'word' stored in meta for grammar questions *should* be that full content string.
        # Let's verify: In generate_word_quiz, for grammar, 'content_to_use' is passed as first arg to generate_single_question.
        # generate_single_question returns { "word": word, ... }.
        # So yes, meta['word'] holds the content used for generation.
        
        new_q_result = await word_training_service.generate_single_question(word, template)
        
        if not new_q_result.get("success"):
            raise ValueError(f"Generation failed: {new_q_result.get('error')}")
            
        # Parse content
        content_json = json.loads(new_q_result["question_content"])
        
        # Normalize keys (same logic as in quiz.py)
        q_text = content_json.get("question") or content_json.get("question_text")
        raw_options = content_json.get("options")
        answer = content_json.get("answer") or content_json.get("correct_answer")
        
        import re
        final_options = None
        if isinstance(raw_options, list) and raw_options:
            final_options = {}
            for idx, opt in enumerate(raw_options):
                key = chr(65 + idx)
                clean_opt = re.sub(r'^[A-D][\.\s\、]+', '', str(opt)).strip()
                final_options[key] = clean_opt
        elif isinstance(raw_options, dict) and raw_options:
            final_options = {}
            for k, v in raw_options.items():
                clean_opt = re.sub(r'^[A-D][\.\s\、]+', '', str(v)).strip()
                final_options[k] = clean_opt
                
        final_answer = answer
        if final_options and isinstance(answer, str):
            if answer in final_options:
                final_answer = answer
            else:
                for k, v in final_options.items():
                    if v.strip() == answer.strip():
                        final_answer = k
                        break
        
        return {
            "question_text": q_text,
            "quiz_type": content_json.get("quiz_type", "choice" if final_options else "blank"),
            "options": final_options if final_options else [],
            "correct_answer": final_answer,
            "explanation": "",
            "meta": {
                "word": new_q_result["word"],
                "prompt": new_q_result["prompt"]
            }
        }

    @staticmethod
    def get_wrong_questions(
        db: Session,
        user_id: int,
        chapter_id: Optional[int] = None,
        section_id: Optional[int] = None,
        subsection_id: Optional[int] = None,
        is_mastered: Optional[bool] = None,
        practice_mode: Optional[str] = None,
        limit: int = 20
    ) -> List[WrongQuestion]:
        """
        获取错题列表

        Args:
            db: 数据库会话
            user_id: 用户ID
            chapter_id: 章节ID（可选）
            section_id: 节ID（可选）
            subsection_id: 小节ID（可选）
            is_mastered: 是否已掌握（可选）
            practice_mode: 练习模式（可选：chapter/random）
            limit: 返回数量限制

        Returns:
            List[WrongQuestion]: 错题列表
        """
        from app.models.subsection import SubSection
        from app.models.quiz import QuizRecord
        
        # Start with a join to QuizRecord if we need to filter by practice_mode
        # But practice_mode is not in QuizRecord directly? YES it is.
        # But WrongQuestion has quiz_record_id.
        query = db.query(WrongQuestion).join(QuizRecord).filter(WrongQuestion.user_id == user_id)

        if chapter_id:
            query = query.filter(WrongQuestion.chapter_id == chapter_id)
        
        if section_id:
             # Logic change:
             # If filtering by section_id, we want questions that belong to this section.
             # This includes:
             # 1. Questions with subsection_id belonging to this section.
             # 2. Questions with section_id equal to this section (Comprehensive).
             
             # But if practice_mode is specified, we narrow it down.
             
             subsections = db.query(SubSection.id).filter(SubSection.section_id == section_id).all()
             sub_ids = [s[0] for s in subsections] if subsections else []
             
             conditions = []
             if sub_ids:
                 conditions.append(WrongQuestion.subsection_id.in_(sub_ids))
             
             # Also include questions directly linked to section (new logic)
             conditions.append(WrongQuestion.section_id == section_id)
             
             from sqlalchemy import or_
             query = query.filter(or_(*conditions))

        if subsection_id:
            query = query.filter(WrongQuestion.subsection_id == subsection_id)

        if is_mastered is not None:
            query = query.filter(WrongQuestion.is_mastered == (1 if is_mastered else 0))
            
        if practice_mode:
            # Filter by practice_mode in QuizRecord
            # 'chapter' mode in frontend maps to 'chapter' or 'subsection' in DB
            if practice_mode == 'chapter':
                 query = query.filter(QuizRecord.practice_mode.in_(['chapter', 'subsection']))
            elif practice_mode == 'random': # comprehensive in frontend maps to random
                 query = query.filter(QuizRecord.practice_mode == 'random')
            else:
                 query = query.filter(QuizRecord.practice_mode == practice_mode)

        # 按创建时间倒序
        records = query.order_by(WrongQuestion.created_at.desc()).limit(limit).all()

        return records

    @staticmethod
    def get_weak_knowledge_points(
        db: Session,
        user_id: int,
        chapter_id: Optional[int] = None,
        top_k: int = 5
    ) -> List[Dict[str, Any]]:
        """
        统计薄弱知识点

        Args:
            db: 数据库会话
            user_id: 用户ID
            chapter_id: 章节ID（可选）
            top_k: 返回前K个薄弱点

        Returns:
            List[Dict]: 薄弱知识点统计
        """
        query = db.query(WrongQuestion).filter(
            WrongQuestion.user_id == user_id,
            WrongQuestion.is_mastered == 0,
            WrongQuestion.knowledge_point_ids.isnot(None)
        )

        if chapter_id:
            query = query.filter(WrongQuestion.chapter_id == chapter_id)

        wrong_questions = query.all()

        # 统计每个知识点的错误次数
        kp_stats = {}
        for wq in wrong_questions:
            if not wq.knowledge_point_ids:
                continue

            try:
                kp_ids = json.loads(wq.knowledge_point_ids)
                if not isinstance(kp_ids, list):
                    continue

                for kp_id in kp_ids:
                    if kp_id not in kp_stats:
                        kp_stats[kp_id] = {
                            "knowledge_point_id": kp_id,
                            "error_count": 0,
                            "avg_score": 0,
                            "scores": []
                        }
                    kp_stats[kp_id]["error_count"] += 1
                    kp_stats[kp_id]["scores"].append(wq.score)
            except json.JSONDecodeError:
                logger.warning(f"Invalid JSON in knowledge_point_ids: {wq.knowledge_point_ids}")
                continue

        # 计算平均分
        for kp_id, stats in kp_stats.items():
            scores = stats["scores"]
            stats["avg_score"] = sum(scores) / len(scores) if scores else 0
            del stats["scores"]  # 移除临时字段

        # 按错误次数排序
        sorted_stats = sorted(
            kp_stats.values(),
            key=lambda x: (-x["error_count"], x["avg_score"])
        )

        return sorted_stats[:top_k]

    @staticmethod
    def update_mastery_status(
        db: Session,
        wrong_question_id: int,
        is_mastered: bool,
        retry_score: Optional[float] = None
    ) -> bool:
        """
        更新错题掌握状态

        Args:
            db: 数据库会话
            wrong_question_id: 错题ID
            is_mastered: 是否已掌握
            retry_score: 重做得分

        Returns:
            bool: 是否成功
        """
        wrong_q = db.query(WrongQuestion).filter(
            WrongQuestion.id == wrong_question_id
        ).first()

        if not wrong_q:
            return False

        wrong_q.is_mastered = 1 if is_mastered else 0
        wrong_q.retry_count += 1

        if retry_score is not None:
            wrong_q.last_retry_score = retry_score

        wrong_q.last_retry_at = datetime.utcnow()

        db.commit()
        logger.info(f"Updated wrong question {wrong_question_id} mastery status")

        return True

    @staticmethod
    def create_review_quiz(
        db: Session,
        user_id: int,
        chapter_id: Optional[int] = None,
        question_count: int = 5
    ) -> Dict[str, Any]:
        """
        创建错题重练练习

        从用户未掌握的错题中随机选择

        Returns:
            Dict: {
                "questions": [...],
                "wrong_question_ids": [...],
                "chapter_id": int (optional)
            }
        """
        from sqlalchemy import func

        query = db.query(WrongQuestion).filter(
            WrongQuestion.user_id == user_id,
            WrongQuestion.is_mastered == 0
        )

        if chapter_id:
            query = query.filter(WrongQuestion.chapter_id == chapter_id)

        # 随机选择未掌握的错题
        # 优先选择重做次数少的题目，但加入随机性
        wrong_questions = query.order_by(
            WrongQuestion.retry_count.asc(),
            func.random()  # 加入随机性
        ).limit(question_count).all()

        if not wrong_questions:
            return {
                "questions": [],
                "wrong_question_ids": [],
                "chapter_id": chapter_id
            }

        questions = []
        wq_ids = []

        for wq in wrong_questions:
            try:
                question_data = json.loads(wq.question_data) if wq.question_data else {}
                # 确保包含 question_type 字段，供前端显示题型标签
                question_data['question_type'] = wq.question_type
                questions.append(question_data)
                wq_ids.append(wq.id)
            except json.JSONDecodeError:
                logger.warning(f"Invalid JSON in question_data for wrong_question {wq.id}")
                continue

        return {
            "questions": questions,
            "wrong_question_ids": wq_ids,
            "chapter_id": chapter_id,
            "total_available": query.count()  # 添加可用错题总数
        }

    @staticmethod
    def submit_review_quiz(
        db: Session,
        user_id: int,
        wrong_question_ids: List[int],
        user_answers: List[Any]
    ) -> Dict[str, Any]:
        """
        提交错题重练答案

        检查答案正确性，正确的题目自动标记为已掌握

        Args:
            db: 数据库会话
            user_id: 用户ID
            wrong_question_ids: 错题ID列表
            user_answers: 用户答案列表

        Returns:
            Dict: 批改结果
        """
        if len(wrong_question_ids) != len(user_answers):
            raise ValueError("答案数量与题目数量不符")

        # 获取错题记录
        wrong_questions = db.query(WrongQuestion).filter(
            WrongQuestion.id.in_(wrong_question_ids),
            WrongQuestion.user_id == user_id
        ).all()

        wq_map = {wq.id: wq for wq in wrong_questions}

        results = []
        correct_count = 0
        total_score = 0.0

        for wq_id, user_answer in zip(wrong_question_ids, user_answers):
            wq = wq_map.get(wq_id)
            if not wq:
                continue

            # 解析题目数据
            try:
                question_data = json.loads(wq.question_data) if wq.question_data else {}
            except json.JSONDecodeError:
                continue

            correct_answer = question_data.get('correct_answer')

            # 检查答案（使用quiz_service的逻辑）
            from app.services.quiz_service import QuizService
            is_correct, item_score, feedback = QuizService._check_answer(
                user_answer=user_answer,
                correct_answer=correct_answer,
                quiz_type=wq.question_type,
                question=question_data.get('question', '')
            )

            if is_correct:
                correct_count += 1

            total_score += item_score

            # 更新错题状态
            wq.retry_count += 1
            wq.last_retry_score = item_score
            wq.last_retry_at = datetime.utcnow()

            # 如果答对了，标记为已掌握
            if is_correct:
                wq.is_mastered = 1
                logger.info(f"Wrong question {wq_id} marked as mastered")

            results.append({
                "wrong_question_id": wq_id,
                "user_answer": user_answer,
                "correct_answer": correct_answer,
                "is_correct": is_correct,
                "score": round(item_score, 3),
                "feedback": feedback,
                "newly_mastered": is_correct  # 标记是否新掌握
            })

        db.commit()

        # 计算统计数据
        total_count = len(results)
        accuracy = (correct_count / total_count * 100) if total_count > 0 else 0
        score = (total_score / total_count * 100) if total_count > 0 else 0

        newly_mastered_count = sum(1 for r in results if r['newly_mastered'])

        logger.info(f"Review quiz submitted: user={user_id}, score={score:.2f}, newly_mastered={newly_mastered_count}")

        return {
            "score": score,
            "accuracy": accuracy,
            "correct_count": correct_count,
            "total_count": total_count,
            "newly_mastered_count": newly_mastered_count,
            "results": results
        }


# 创建全局实例
wrong_question_service = WrongQuestionService()
