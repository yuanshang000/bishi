"""
练习服务

提供练习题目生成、提交、批改等功能
"""

from typing import List, Dict, Any, Optional
from sqlalchemy.orm import Session
from fastapi import HTTPException, status
from datetime import datetime
import json
import logging

from app.models.quiz import QuizRecord
from app.models.chapter import Chapter
from app.models.section import Section
from app.models.subsection import SubSection
from app.models.wrong_question import WrongQuestion
from app.models.knowledge_point import KnowledgePoint
from app.models.user_knowledge_stats import UserKnowledgePointStats
from app.models.user_word_stats import UserWordStats
from app.models.document import CourseDocument
from app.services.llm_service import llm_service
from app.core.config import settings
from app.services.rag_service import rag_service

logger = logging.getLogger(__name__)


class QuizService:
    """练习服务类"""

    @staticmethod
    async def create_quiz(
        db: Session,
        user_id: int,
        quiz_type: str,
        question_count: int = 5,
        practice_mode: str = "chapter",
        chapter_id: Optional[int] = None,
        subsection_id: Optional[int] = None,
        knowledge_point_ids: Optional[List[str]] = None,
        difficulty: str = "intermediate"
    ) -> QuizRecord:
        """
        创建练习

        Args:
            db: 数据库会话
            user_id: 用户ID
            quiz_type: 练习类型
            question_count: 题目数量
            practice_mode: 练习方式 (chapter/subsection/random/comprehensive)
            chapter_id: 章节ID（章节练习时必填）
            subsection_id: 小目标ID（小目标练习时必填）
            knowledge_point_ids: 指定知识点ID列表（可选）
            difficulty: 难度等级 (easy/intermediate/hard)

        Returns:
            QuizRecord: 练习记录

        Raises:
            HTTPException: 章节不存在或生成失败时抛出
        """
        # 验证参数
        if practice_mode == "chapter" and not chapter_id:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="章节练习需要提供章节ID"
            )
        if practice_mode == "subsection" and not subsection_id:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="小目标练习需要提供小目标ID"
            )

        # 获取上下文
        context = ""
        used_documents = []
        used_chunks = []

        if practice_mode == "chapter":
            # 章节练习：检查章节是否存在
            chapter = db.query(Chapter).filter(Chapter.id == chapter_id).first()
            if not chapter:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="章节不存在"
                )

            # 如果用户在章节练习中选择了具体小节，则优先使用该小节的向量化内容
            applied_rules_text = ""
            use_built_in_rules = False
            if subsection_id:
                try:
                    # 获取小节上下文（仅该小节的向量化内容）
                    context, used_documents, used_chunks = rag_service.get_context_for_subsection(
                        subsection_id=subsection_id,
                        max_length=3000,
                        top_k=6
                    )

                    # 获取该小节的知识点，供内置规则使用
                    knowledge_points = db.query(KnowledgePoint).filter(
                        KnowledgePoint.subsection_id == subsection_id
                    ).all()

                    # 构建规则预览文本（仅展示与当前选择相关的内容）
                    words_count = len([kp for kp in knowledge_points if kp.type == "word"])
                    grammar_count = len([kp for kp in knowledge_points if kp.type == "grammar"])
                    phrases_count = len([kp for kp in knowledge_points if kp.type == "phrase"])
                    diff_map = {"easy": "简单", "intermediate": "中等", "hard": "困难"}
                    diff_cn = diff_map.get(difficulty, difficulty)

                    lines = [f"难度：{diff_cn}"]
                    if words_count > 0:
                        vc = 2 * words_count if words_count < 5 else words_count
                        lines.append(f"词汇：目标词汇 {words_count} 个 → 题数约 {vc}")
                    if grammar_count > 0:
                        lines.append(f"语法：目标语法 {grammar_count} 个 → 每个 3 题，共 {3 * grammar_count}")
                    if phrases_count > 0:
                        lines.append(f"固定搭配：目标短语 {phrases_count} 个 → 每个 1 题，共 {phrases_count}")
                    # 仅当三个列表均有内容且难度为中/难时提示综合运用
                    if words_count > 0 and grammar_count > 0 and phrases_count > 0 and difficulty != "easy":
                        lines.append("综合运用：生成 1 个微型语篇并派生 3-5 题")
                    applied_rules_text = "\n".join(lines)

                    use_built_in_rules = len(knowledge_points) > 0
                except Exception as e:
                    logger.error(f"Error preparing subsection context/rules: {e}")
                    # 回退到章节级检索
                    context, used_documents, used_chunks = rag_service.get_context_for_query(
                        query=f"Chapter {chapter.chapter_number}: {chapter.title}",
                        chapter_id=chapter_id,
                        max_length=3000
                    )
            else:
                # 未选择小节：使用章节级RAG上下文
                # 如果指定了知识点，优先使用知识点相关内容（待优化）
                if knowledge_point_ids:
                    logger.info(f"Creating quiz for knowledge points: {knowledge_point_ids}")

                context, used_documents, used_chunks = rag_service.get_context_for_query(
                    query=f"Chapter {chapter.chapter_number}: {chapter.title}",
                    chapter_id=chapter_id,
                    max_length=3000
                )

                if not context:
                    # 如果没有检索到内容，使用章节描述
                    context = f"""
章节 {chapter.chapter_number}: {chapter.title}

{chapter.description or ''}

学习目标：
{chapter.learning_objectives or ''}

知识点：
{chapter.key_points or ''}
"""
                    used_documents = []
                    used_chunks = []

        elif practice_mode == "subsection":
            # 小目标练习
            subsection = db.query(SubSection).filter(SubSection.id == subsection_id).first()
            if not subsection:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="小目标不存在"
                )
            
            section = db.query(Section).filter(Section.id == subsection.section_id).first()
            chapter = db.query(Chapter).filter(Chapter.id == section.chapter_id).first()

            # 获取该用户在该小目标下的错题记录
            wrong_questions = db.query(WrongQuestion).filter(
                WrongQuestion.user_id == user_id,
                WrongQuestion.subsection_id == subsection_id,
                WrongQuestion.is_mastered == False
            ).all()

            wrong_questions_context = ""
            if wrong_questions:
                wrong_questions_context = "\n【重点关注 - 历史错题】\n学生在以下题目上曾犯错，请生成类似的变式题进行强化训练：\n"
                for i, wq in enumerate(wrong_questions[:5], 1):  # 最多参考5道错题
                    wrong_questions_context += f"{i}. {wq.question_content} (错误答案: {wq.wrong_answer})\n"

            # 解析出题要求，生成更清晰的指令
            req_instruction = ""
            if subsection.requirements:
                try:
                    req_data = json.loads(subsection.requirements)
                    req_instruction = "\n【特别指令 (High Priority)】\n请优先满足以下要求：\n"
                    
                    # 提取关键指令字段
                    if "focus" in req_data:
                        req_instruction += f"- 重点考察：{req_data['focus']}\n"
                    if "description" in req_data:
                        req_instruction += f"- 详细说明：{req_data['description']}\n"
                    if "constraints" in req_data:
                        req_instruction += f"- 限制条件：{req_data['constraints']}\n"
                    if "keywords" in req_data:
                        req_instruction += f"- 必须包含关键词：{req_data['keywords']}\n"
                    if "grammar" in req_data:
                        req_instruction += f"- 必须包含语法点：{req_data['grammar']}\n"
                    if "sentence_structure" in req_data:
                        req_instruction += f"- 指定句型：{req_data['sentence_structure']}\n"
                        
                except json.JSONDecodeError:
                    pass

            context = f"""
【背景信息】
章节：{chapter.title}
小节：{section.title}
小目标：{subsection.title}

【学习内容】
{subsection.content or '暂无内容'}

【出题要求 (原始数据)】
{subsection.requirements or '暂无特殊要求'}

{req_instruction}

{wrong_questions_context}

请严格遵循【特别指令】（如果有）和【出题要求】生成题目。
"""

        elif practice_mode == "random":
            # 随机练习：从所有章节随机获取内容
            context, used_documents, used_chunks = rag_service.get_context_for_query(
                query=f"Generate random {quiz_type} questions",
                chapter_id=None,  # 不限制章节
                max_length=3000
            )

            if not context:
                # 通过数据库直接读取部分课程文档作为上下文（避免空上下文导致LLM无法生成）
                logger.info("RAG未检索到内容，改为从数据库读取文档构建随机上下文")
                docs = db.query(CourseDocument).filter(CourseDocument.content.isnot(None)).order_by(CourseDocument.id.desc()).limit(3).all()
                if docs:
                    parts = []
                    used_documents = []
                    used_chunks = []
                    total = 0
                    for d in docs:
                        text = (d.content or "").strip()
                        if not text:
                            continue
                        # 每个文档截取最多1000字符，控制总长度不超过3000
                        take = min(1000, 3000 - total)
                        if take <= 0:
                            break
                        snippet = text[:take]
                        parts.append(snippet)
                        total += len(snippet)
                        used_documents.append({
                            "document_id": d.id,
                            "title": d.title,
                            "doc_type": d.doc_type.value if hasattr(d.doc_type, "value") else str(d.doc_type)
                        })
                        used_chunks.append({
                            "index": len(used_chunks),
                            "length": len(snippet),
                            "preview": snippet[:200] + ("..." if len(snippet) > 200 else ""),
                            "document_id": d.id,
                            "title": d.title,
                            "doc_type": d.doc_type.value if hasattr(d.doc_type, "value") else str(d.doc_type),
                            "score": 0
                        })
                    context = "\n\n---\n\n".join(parts)
                else:
                    context = f"大学英语课程常见词汇与语法练习材料，用于生成随机{quiz_type}题目。"

        elif practice_mode == "comprehensive":
            # 综合练习：基于AI学情分析的薄弱知识点
            # 这里暂时使用通用上下文，后续会在AI分析中实现针对性出题
            context, used_documents, used_chunks = rag_service.get_context_for_query(
                query=f"Generate comprehensive {quiz_type} questions based on weak points",
                chapter_id=None,
                max_length=3000
            )

            if not context:
                context = f"生成综合{quiz_type}类型的练习题目"

        # 记录上下文信息用于调试
        logger.info(f"Context length for quiz generation: {len(context)} chars")
        logger.info(f"Using {len(used_documents)} documents for quiz generation")

        # 输出检索到的文档列表
        if used_documents:
            logger.info("Used documents:")
            for i, doc in enumerate(used_documents, 1):
                logger.info(f"  {i}. [{doc.get('doc_type')}] {doc.get('title')} (ID: {doc.get('document_id')})")

        # 输出上下文预览（前500字符）
        context_preview = context[:500].replace('\n', ' ')
        logger.info(f"Context preview: {context_preview}...")

        # 如果上下文很长，也输出后面的部分
        if len(context) > 500:
            context_end = context[-200:].replace('\n', ' ')
            logger.info(f"Context end: ...{context_end}")

        # 生成题目
        try:
            # 当章节练习选择了具体小节且存在知识点时，启用内置规则生成（遵循出题规则.md）
            if practice_mode == "chapter" and subsection_id and use_built_in_rules:
                knowledge_points = db.query(KnowledgePoint).filter(
                    KnowledgePoint.subsection_id == subsection_id
                ).all()
                questions = llm_service.generate_quiz(
                    context=context,
                    quiz_type="mixed",
                    count=question_count,
                    difficulty=difficulty,
                    target_knowledge_points=knowledge_points
                )
                # 将quiz_type覆盖为mixed以便前端显示综合题型
                quiz_type = "mixed"
            else:
                questions = llm_service.generate_quiz(
                    context=context,
                    quiz_type=quiz_type,
                    count=question_count,
                    difficulty=difficulty
                )

            if not questions:
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail="题目生成失败"
                )

            # 创建练习记录
            quiz_record = QuizRecord(
                user_id=user_id,
                chapter_id=chapter_id,
                subsection_id=subsection_id,
                practice_mode=practice_mode,
                quiz_type=quiz_type,
                score=0,
                question_count=len(questions),
                questions=json.dumps(questions, ensure_ascii=False),
                knowledge_point_ids=json.dumps(knowledge_point_ids, ensure_ascii=False) if knowledge_point_ids else None,
                started_at=datetime.utcnow(),
            )

            db.add(quiz_record)
            db.commit()
            db.refresh(quiz_record)

            logger.info(f"Quiz created: ID={quiz_record.id}, type={quiz_type}, questions={len(questions)}")

            # 将使用的文档信息附加到quiz_record对象（临时属性，不保存到数据库）
            quiz_record.source_documents = used_documents
            quiz_record.source_chunks = used_chunks
            quiz_record.rag_context = context
            if applied_rules_text:
                quiz_record.applied_rules = applied_rules_text

            return quiz_record

        except HTTPException:
            # 直接重新抛出 HTTPException，保留详细错误信息
            db.rollback()
            raise
        except Exception as e:
            # 其他异常
            db.rollback()
            logger.error(f"Error creating quiz: {e}", exc_info=True)
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"创建练习失败: {str(e)}"
            )

    @staticmethod
    def submit_quiz(
        db: Session,
        quiz_id: int,
        user_id: int,
        user_answers: List[Any],
        time_spent: Optional[int] = None
    ) -> Dict[str, Any]:
        """
        提交练习答案

        Args:
            db: 数据库会话
            quiz_id: 练习ID
            user_id: 用户ID
            user_answers: 用户答案列表
            time_spent: 用时（秒）

        Returns:
            Dict: 批改结果

        Raises:
            HTTPException: 练习不存在或已完成时抛出
        """
        # 获取练习记录
        quiz = db.query(QuizRecord).filter(
            QuizRecord.id == quiz_id,
            QuizRecord.user_id == user_id
        ).first()

        if not quiz:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="练习不存在"
            )

        if quiz.is_completed:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="练习已完成，不能重复提交"
            )

        # 解析题目和答案
        questions = json.loads(quiz.questions) if quiz.questions else []

        if len(user_answers) != len(questions):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="答案数量与题目数量不符"
            )

        # 批改答案
        correct_count = 0
        total_score = 0.0
        results = []
        
        # 缓存本次提交中涉及的 UserKnowledgePointStats 对象，避免重复查询/创建导致的主键冲突或重复数据
        stats_cache = {}

        for i, (question, user_answer) in enumerate(zip(questions, user_answers)):
            correct_answer = question.get('correct_answer')
            # 优先获取 'question' 字段作为题目内容
            # 如果 'question' 为空，尝试其他可能的字段 (兼容旧数据或特殊题型)
            question_text = question.get('question', '')
            if not question_text:
                if question.get('title'):
                    question_text = question.get('title')
                elif question.get('content'):
                    question_text = question.get('content')
                # 再次尝试从 meta.prompt 中解析 (兼容 WordTrainingService 生成的数据)
                elif question.get('meta') and question.get('meta').get('prompt'):
                    # 尝试从 prompt 中提取题目 (这是一个临时方案，最好是生成时就存好)
                    # WordTrainingService 的 prompt 格式通常包含 "题目为选择题...题目内容应结合实际...出题形式例如：..."
                    # 但 prompt 是给 AI 的指令，不是题目本身。
                    # 真正的题目应该是 question_text 字段。
                    # 如果 question_text 为空，说明生成或保存时出了问题。
                    # 但既然用户提到了 question_text 在 Terminal#337-349 是 'My neighbor usually ______...'
                    # 那说明数据本身是有 question_text 的。
                    # 这里的代码逻辑看似没问题：question_text = question.get('question', '')
                    # 为什么还会取不到呢？
                    # 可能是因为 question 字典里的 key 不叫 'question'？
                    # 但日志显示：Data: {'question_text': 'My neighbor usually...', ...}
                    # 注意：日志里的 key 是 'question_text' 而不是 'question'！
                    if question.get('question_text'):
                        question_text = question.get('question_text')

            # 记录调试日志
            if not question_text:
                 logger.warning(f"Question {i} has empty text! Data: {question}")
            
            # 获取题目类型（优先使用question级别的quiz_type，用于综合练习）
            # 综合练习中每个题目可能有不同的类型
            question_quiz_type = question.get('quiz_type', quiz.quiz_type)

            # 调用新的_check_answer方法，返回三元组
            is_correct, item_score, feedback = QuizService._check_answer(
                user_answer=user_answer,
                correct_answer=correct_answer,
                quiz_type=question_quiz_type,  # 使用question级别的quiz_type
                question=question_text,
                extra_info=question  # 传递完整的题目信息
            )

            if is_correct:
                correct_count += 1

            total_score += item_score

            # -----------------------------------------------------------------
            # 智能分批策略：更新知识点分数 (Knowledge Point Score Update)
            # -----------------------------------------------------------------
            target_item = question.get('target_item')
            
            # Fallback: 如果没有 target_item，尝试从 meta 中获取 word (兼容 WordTrainingService)
            if not target_item:
                meta = question.get('meta', {})
                if meta and meta.get('word'):
                    target_item = meta.get('word')

            if target_item:
                logger.info(f"Processing knowledge point stats for target_item: {target_item}")
                kp = None
                
                # 辅助函数：根据条件查找 KP
                def find_kp(t_item):
                    if not t_item:
                        return None
                        
                    # 预处理：去除首尾空格
                    t_item = t_item.strip()
                    
                    # 定义查找逻辑 (封装以便复用于带scope和不带scope的情况)
                    def search_logic(query_base):
                        # 1. 精确匹配 (Case-insensitive)
                        # SQLite 默认 case-insensitive for ASCII, 但为了保险使用 func.lower
                        from sqlalchemy import func
                        found = query_base.filter(func.lower(KnowledgePoint.content) == func.lower(t_item)).first()
                        if found:
                            return found
                        
                        # 2. 尝试前缀匹配 (e.g. "apple" -> "apple (n. 苹果)")
                        # 仅当 t_item 是纯英文单词时尝试
                        if t_item.replace(" ", "").isalpha():
                             # Case-insensitive prefix match
                             found = query_base.filter(KnowledgePoint.content.ilike(f"{t_item} %")).first()
                             if found:
                                 return found
                             found = query_base.filter(KnowledgePoint.content.ilike(f"{t_item}(%")).first()
                             if found:
                                 return found

                        # 3. 尝试包含匹配 (e.g. "apple (n. 苹果)" -> "apple")
                        # 提取 t_item 中的英文单词
                        import re
                        match = re.match(r'^([a-zA-Z\s\-]+)', t_item)
                        if match:
                            core_word = match.group(1).strip()
                            if core_word and len(core_word) > 2:
                                # Try to match if KP content starts with this core word
                                found = query_base.filter(KnowledgePoint.content.ilike(f"{core_word}%")).first()
                                if found:
                                    return found
                        
                        # 4. Try matching the first line (for Grammar KPs where content might be multiline in target_item)
                        if "\n" in t_item:
                            first_line = t_item.split("\n")[0].strip()
                            # Try exact match of first line
                            found = query_base.filter(KnowledgePoint.content == first_line).first()
                            if found:
                                return found
                            # Try prefix match of first line
                            found = query_base.filter(KnowledgePoint.content.ilike(f"{first_line}%")).first()
                            if found:
                                return found

                        return None

                    # 策略1：在当前Scope（小节/章节）内查找
                    query = db.query(KnowledgePoint)
                    if quiz.subsection_id:
                        query = query.filter(KnowledgePoint.subsection_id == quiz.subsection_id)
                    elif quiz.chapter_id:
                        query = query.join(SubSection).join(Section).filter(Section.chapter_id == quiz.chapter_id)
                    
                    kp_found = search_logic(query)
                    if kp_found:
                        return kp_found
                        
                    # 策略2：如果Scope内没找到，尝试全局查找 (Fallback)
                    # 有时候题目生成的知识点可能属于其他章节（或者是复习题）
                    logger.info(f"KP '{t_item}' not found in scope, trying global search...")
                    kp_found = search_logic(db.query(KnowledgePoint))
                    
                    return kp_found

                kp = find_kp(target_item)
                
                if kp:
                    logger.info(f"Found KnowledgePoint ID: {kp.id} for {target_item}")
                    
                    # 2. 更新或创建用户知识点统计 (UserKnowledgePointStats)
                    # 优先从缓存获取，避免同一批次提交中重复创建
                    cache_key = f"{user_id}_{kp.id}"
                    user_kp_stat = stats_cache.get(cache_key)
                    
                    if not user_kp_stat:
                        user_kp_stat = db.query(UserKnowledgePointStats).filter(
                            UserKnowledgePointStats.user_id == user_id,
                            UserKnowledgePointStats.knowledge_point_id == kp.id
                        ).first()

                        if not user_kp_stat:
                            user_kp_stat = UserKnowledgePointStats(
                                user_id=user_id,
                                knowledge_point_id=kp.id,
                                total_attempts=0,
                                correct_attempts=0,
                                consecutive_errors=0,
                                consecutive_corrects=0,
                                mastery_score=0.0
                            )
                            db.add(user_kp_stat)
                        
                        # 加入缓存
                        stats_cache[cache_key] = user_kp_stat
                    
                    # 更新统计数据
                    user_kp_stat.total_attempts += 1
                    user_kp_stat.last_reviewed_at = datetime.utcnow()

                    if item_score >= 0.9:
                        # 做对 (Correct)
                        user_kp_stat.correct_attempts += 1
                        user_kp_stat.consecutive_errors = 0
                        user_kp_stat.consecutive_corrects += 1
                        # 掌握度加分 (简单算法)
                        user_kp_stat.mastery_score = min(100.0, user_kp_stat.mastery_score + 10.0)
                    elif item_score >= 0.4:
                        # 半对 (Half-correct)
                        user_kp_stat.consecutive_errors = 0
                        user_kp_stat.consecutive_corrects = 0
                        user_kp_stat.mastery_score = max(0.0, user_kp_stat.mastery_score - 5.0)
                    else:
                        # 做错 (Wrong)
                        user_kp_stat.consecutive_errors += 1
                        user_kp_stat.consecutive_corrects = 0
                        user_kp_stat.mastery_score = max(0.0, user_kp_stat.mastery_score - 15.0)
                    
                    # 同时也更新 KnowledgePoint 表的总体统计 (可选，作为全局参考)
                    # A. 防死循环机制 (Anti-Death-Loop)
                    if kp.consecutive_errors >= 3:
                        # 强制冷却
                        kp.priority_score += 5.0
                        kp.consecutive_errors = 0
                        logger.info(f"KnowledgePoint '{target_item}' triggered anti-death-loop. Score += 5.0")
                    else:
                        # B. 基础分数变更
                        if item_score >= 0.9:
                            kp.consecutive_errors = 0
                            kp.correct_attempts += 1
                        elif item_score >= 0.4:
                            kp.priority_score -= 0.5
                            kp.consecutive_errors = 0
                        else:
                            kp.priority_score -= 1.0
                            kp.consecutive_errors += 1
                    
                    kp.total_attempts += 1
                    kp.last_reviewed_at = datetime.utcnow()
                    db.add(kp) # Mark as modified
            
            # -----------------------------------------------------------------
            # Word Training Stats Update (UserWordStats)
            # -----------------------------------------------------------------
            meta = question.get('meta', {})
            word = meta.get('word')
            if word and quiz.subsection_id:
                 from app.services.word_training_service import word_training_service
                 word_training_service.update_stats_after_submission(
                     db=db,
                     user_id=user_id,
                     word=word,
                     is_correct=is_correct,
                     subsection_id=quiz.subsection_id
                 )

            results.append({
                "question_index": i,
                "user_answer": user_answer,
                "correct_answer": correct_answer,
                "is_correct": is_correct,
                "score": round(item_score, 3),  # 新增：具体分数
                "feedback": feedback,  # 新增：评语
                "explanation": question.get('explanation', '')
            })

        # 计算分数和正确率
        total_count = len(questions)
        accuracy = (correct_count / total_count * 100) if total_count > 0 else 0
        # 使用平均分数作为总分（0-100）
        score = (total_score / total_count * 100) if total_count > 0 else 0

        # 计算用时
        final_time_spent = 0
        if time_spent is not None:
             final_time_spent = time_spent
        elif quiz.started_at:
            final_time_spent = int((datetime.utcnow() - quiz.started_at).total_seconds())

        # 更新练习记录
        quiz.user_answers = json.dumps(user_answers, ensure_ascii=False)
        quiz.correct_answers = json.dumps(
            [q.get('correct_answer') for q in questions],
            ensure_ascii=False
        )
        quiz.results = json.dumps(results, ensure_ascii=False)  # 保存详细结果
        quiz.score = score
        quiz.accuracy = accuracy
        quiz.time_spent = final_time_spent
        quiz.is_completed = 1
        quiz.completed_at = datetime.utcnow()

        db.commit()

        logger.info(f"Quiz submitted: ID={quiz_id}, score={score:.2f}, accuracy={accuracy:.2f}%")

        # 自动记录错题
        wrong_results = [r for r in results if not r['is_correct']]
        if wrong_results:
            try:
                from app.services.wrong_question_service import wrong_question_service
                wrong_count = wrong_question_service.record_wrong_questions(db, quiz, wrong_results)
                logger.info(f"Recorded {wrong_count} wrong questions for user {user_id}")
            except Exception as e:
                logger.error(f"Error recording wrong questions: {e}")
                # 不影响主流程，继续执行

        return {
            "quiz_id": quiz_id,
            "score": score,
            "accuracy": accuracy,
            "correct_count": correct_count,
            "total_count": total_count,
            "time_spent": final_time_spent,
            "results": results,
            "wrong_count": len(wrong_results)  # 新增：错题数量
        }

    @staticmethod
    def _check_answer(
        user_answer: Any,
        correct_answer: Any,
        quiz_type: str,
        question: Optional[str] = None,
        extra_info: Optional[dict] = None
    ) -> tuple[bool, float, Optional[str]]:
        """
        检查答案是否正确
        
        Args:
            extra_info: 额外的题目信息（如解析、知识点等），用于辅助AI判分


        Args:
            user_answer: 用户答案
            correct_answer: 正确答案
            quiz_type: 题目类型 (reading/translation/writing)
            question: 题目内容（用于语义评分）

        Returns:
            tuple: (is_correct, score, feedback)
            - is_correct: 是否正确（用于统计）
            - score: 具体分数（0-1）
            - feedback: 评语（可选）
        """
        # 1. 确定真实题目类型 (处理综合题/随机题的情况)
        real_quiz_type = quiz_type
        # 定义客观题类型列表
        objective_types = ["reading", "choice", "vocabulary", "blank", "matching", "ordering"]
        
        if extra_info:
            # 如果 extra_info 中明确指定了 quiz_type，直接使用
            if extra_info.get('quiz_type'):
                real_quiz_type = extra_info.get('quiz_type')
            # 否则尝试根据 extra_info 的字段特征推断
            elif not any(t in quiz_type for t in objective_types + ["translation", "writing"]):
                if extra_info.get('options') or extra_info.get('items') or extra_info.get('pairs'):
                    if extra_info.get('passage'):
                        real_quiz_type = "reading"
                    elif extra_info.get('pairs'):
                        real_quiz_type = "matching"
                    elif extra_info.get('items'):
                        real_quiz_type = "ordering"
                    else:
                        real_quiz_type = "choice"
                elif extra_info.get('key_points') or extra_info.get('key_points_json'):
                    real_quiz_type = "translation"
                elif extra_info.get('topic') or extra_info.get('word_count'):
                    real_quiz_type = "writing"
                    
        # 判断是否为客观题（阅读、选择、词汇、填空等）
        # 支持带后缀的类型，如 "reading:easy"
        is_objective = False
        for t in objective_types:
            if real_quiz_type == t or real_quiz_type.startswith(t + ":"):
                is_objective = True
                break
        
        if is_objective:
            # 全部使用 AI 判定（满足用户“直接用ai判对错”的要求）
            try:
                logger.info(f"Using direct LLM check for {real_quiz_type}...")
                if user_answer and str(user_answer).strip():
                    # Determine score type based on quiz type and extra info
                    score_type = "short_answer"
                    
                    # Normalize types for checking
                    q_type_str = str(real_quiz_type).lower()
                    target_item_str = str(extra_info.get('target_item', '')).lower() if extra_info else ""
                    extra_type = str(extra_info.get('type', '')).lower() if extra_info else ""
                    
                    # 1. Check for Word/Vocabulary
                    if q_type_str in ["vocabulary", "blank", "word"] or \
                       q_type_str.startswith("vocabulary") or \
                       q_type_str.startswith("word") or \
                       extra_type == 'vocabulary':
                        score_type = "word"
                    
                    # 2. Check for Grammar
                    elif q_type_str in ["grammar"] or \
                         q_type_str.startswith("grammar") or \
                         extra_type == 'grammar' or \
                         "grammar" in target_item_str or \
                         "tense" in target_item_str or \
                         "voice" in target_item_str or \
                         "clause" in target_item_str or \
                         "phrase" in target_item_str:
                         score_type = "grammar"
                    
                    # 3. Fallback for "Choice" type: try to infer from target_item content
                    elif q_type_str == "choice":
                         # Heuristic: If target_item is NOT a single word (contains spaces) and score_type is not "word", try grammar
                         if target_item_str and " " in target_item_str and score_type != "word":
                             score_type = "grammar"
                         # Even if target_item is a single word, if it's a choice question, it might be a grammar question about that word's usage
                         # If we haven't decided on "word" type yet, lean towards "grammar" for detailed feedback if it's a choice question
                         elif score_type == "short_answer":
                             # Check if it is likely a vocabulary question
                             # If target_item is present and is a single word, default to 'word' type
                             if target_item_str and " " not in target_item_str and len(target_item_str) < 20:
                                 score_type = "word"
                             else:
                                 score_type = "grammar"

                    # 构建更完整的 question 字符串，包含知识点信息和选项
                    final_question = question or f"{real_quiz_type} Check"
                    
                    # 添加选项信息，这对于选择题至关重要，否则AI不知道A/B/C/D代表什么
                    # 注意：如果 question 字符串本身已经包含了选项（某些RAG生成的情况），这里可能会重复，
                    # 但为了安全起见，我们还是附加上，AI通常能处理重复信息。
                    if extra_info and (extra_info.get('options') or extra_info.get('choices')):
                        options = extra_info.get('options') or extra_info.get('choices')
                        
                        # 检查 final_question 是否已经包含选项 (简单检查)
                        has_options_in_text = "A." in final_question and "B." in final_question
                        
                        if not has_options_in_text:
                            final_question += "\n\n【选项】："
                            if isinstance(options, dict):
                                for k, v in options.items():
                                    final_question += f"\n{k}. {v}"
                            elif isinstance(options, list):
                                labels = ['A', 'B', 'C', 'D', 'E', 'F']
                                for i, opt in enumerate(options):
                                    label = labels[i] if i < len(labels) else str(i+1)
                                    final_question += f"\n{label}. {opt}"

                    if score_type == "grammar" and extra_info:
                         target_item = extra_info.get('target_item')
                         if target_item:
                             final_question += f"\n\n【核心语法知识点】：{target_item}"
                    elif score_type == "word" and extra_info:
                         target_item = extra_info.get('target_item')
                         # Fallback: 如果没有 target_item，尝试从 meta 中获取 word (兼容 WordTrainingService)
                         if not target_item:
                            meta = extra_info.get('meta', {})
                            if meta and meta.get('word'):
                                target_item = meta.get('word')
                         if target_item:
                             final_question += f"\n\n【核心词汇知识点】：{target_item}"
                    
                    # 记录调试日志，查看最终发送给LLM的问题内容
                    logger.info(f"LLM Scoring - Type: {score_type}, Question: {final_question[:100]}...")

                    result = llm_service.semantic_score(
                        user_answer=str(user_answer),
                        correct_answer=str(correct_answer),
                        question=final_question,
                        score_type=score_type
                    )

                    # 处理返回结果：支持两种格式
                    # 格式1: {"is_correct": true, "feedback": "..."} (grammar, word, listening_check)
                    # 格式2: {"score": 0.75, "feedback": "..."} (translation, short_answer, writing)
                    if 'is_correct' in result:
                        # 格式1：直接使用 is_correct
                        is_correct = result.get('is_correct', False)
                        score = 1.0 if is_correct else 0.0
                    else:
                        # 格式2：根据 score 判断
                        score = result.get('score', 0.0)
                        # score >= 0.6 视为正确
                        is_correct = score >= 0.6

                    feedback = result.get('feedback', "回答正确！" if is_correct else f"回答错误。正确答案是 {correct_answer}")
                    return is_correct, score, feedback
            except Exception as e:
                logger.error(f"Direct LLM check failed: {e}")
                # Fallback to simple comparison if AI fails
                user_ans_str = str(user_answer).strip().upper()
                correct_ans_str = str(correct_answer).strip().upper()
                is_correct = user_ans_str == correct_ans_str
                return is_correct, 1.0 if is_correct else 0.0, "AI复核失败，切换至系统比对。"

        elif quiz_type == "translation":
            # 翻译题：使用AI语义评分
            if not user_answer or str(user_answer).strip() == "":
                return False, 0.0, "未作答"

            try:
                user_text = str(user_answer).strip()
                correct_text = str(correct_answer).strip()

                # 构造包含额外信息的题目描述
                full_question = question or "翻译题"
                if extra_info:
                    key_points = extra_info.get('key_points') or extra_info.get('key_points_json')
                    explanation = extra_info.get('explanation')
                    
                    if key_points:
                        # 尝试解析 key_points
                        if isinstance(key_points, str):
                            try:
                                import json
                                key_points = json.loads(key_points)
                            except:
                                pass
                                
                        if isinstance(key_points, list):
                            full_question += f"\n\n【关键点要求】：{', '.join(str(k) for k in key_points)}"
                        else:
                            full_question += f"\n\n【关键点要求】：{key_points}"
                            
                    if explanation:
                        full_question += f"\n\n【考点解析】：{explanation}"

                # 如果翻译完全相同，直接满分
                if user_text == correct_text:
                    return True, 1.0, "翻译完全正确！"

                # 使用LLM进行语义评分
                try:
                    logger.info(f"Starting LLM translation scoring")
                    result = llm_service.semantic_score(
                        user_answer=user_text,
                        correct_answer=correct_text,
                        question=full_question,
                        score_type="translation"
                    )
                    logger.info(f"LLM translation scoring result: {result}")

                    # Check for LLM failure (default response)
                    if result.get('feedback') == "评分系统暂时不可用，已给予基础分":
                         raise Exception("LLM scoring failed (returned default response)")

                    score = result.get('score', 0.5)
                    is_correct = score >= 0.6  # 60分以上算正确

                    # 构建反馈
                    feedback = result.get('feedback', '')

                    # 添加优点
                    if result.get('strengths'):
                        feedback += "\n\n✅ 优点："
                        for strength in result.get('strengths', []):
                            feedback += f"\n• {strength}"

                    # 添加改进建议
                    if result.get('improvements'):
                        feedback += "\n\n💡 改进建议："
                        for improvement in result.get('improvements', []):
                            feedback += f"\n• {improvement}"

                    logger.info(f"Translation scored: {score:.2f}")
                    return is_correct, score, feedback

                except Exception as llm_error:
                    logger.error(f"LLM translation scoring error: {llm_error}", exc_info=True)

                    # 降级到简单的文本相似度评分
                    import difflib
                    similarity = difflib.SequenceMatcher(None, user_text, correct_text).ratio()

                    if similarity >= 0.8:
                        is_correct = True
                        feedback = f"翻译很好！相似度：{similarity*100:.1f}%（AI评分暂时不可用）"
                    elif similarity >= 0.6:
                        is_correct = True
                        feedback = f"翻译良好，相似度：{similarity*100:.1f}%（AI评分暂时不可用）"
                    else:
                        is_correct = False
                        feedback = f"翻译有待改进，相似度：{similarity*100:.1f}%（AI评分暂时不可用）"

                    logger.info(f"Using fallback similarity scoring: {similarity:.2f}")
                    return is_correct, similarity, feedback

            except Exception as e:
                logger.error(f"Translation scoring error: {e}")
                return False, 0.5, "评分失败，已给予基础分"

        elif real_quiz_type == "writing":
            # 写作题：使用LLM进行详细评分
            if not user_answer or str(user_answer).strip() == "":
                return False, 0.0, "未作答"

            try:
                user_text = str(user_answer).strip()
                word_count = len(user_text.split())

                # 字数检查
                if word_count < 30:
                    return False, 0.2, f"字数严重不足（{word_count}词），无法进行详细评分。建议至少150词。"

                # 使用LLM进行详细评分
                try:
                    logger.info(f"Starting LLM writing scoring, word_count: {word_count}")
                    result = llm_service.semantic_score(
                        user_answer=user_text,
                        correct_answer=str(correct_answer) if correct_answer else "",
                        question=question or "写作题",
                        score_type="writing"
                    )
                    logger.info(f"LLM scoring result: {result}")

                    score = result.get('score', 0.5)
                    is_correct = score >= 0.6

                    # 构建详细的反馈
                    feedback_parts = [result.get('feedback', '')]

                    # 添加优点
                    if result.get('strengths'):
                        feedback_parts.append("\n✅ 优点：")
                        for i, strength in enumerate(result.get('strengths', []), 1):
                            feedback_parts.append(f"{i}. {strength}")

                    # 添加句子改进建议（新增）
                    if result.get('sentence_improvements'):
                        feedback_parts.append("\n\n📝 句子改进建议：")
                        for i, improvement in enumerate(result.get('sentence_improvements', []), 1):
                            feedback_parts.append(f"\n【句子{i}】")
                            feedback_parts.append(f"原句：{improvement.get('original', '')}")
                            feedback_parts.append(f"问题：{improvement.get('issue', '')}")
                            feedback_parts.append(f"改进：{improvement.get('improved', '')}")
                            feedback_parts.append(f"说明：{improvement.get('explanation', '')}")

                    # 添加与范文对比（新增）
                    if result.get('comparison_with_sample'):
                        feedback_parts.append("\n\n📖 与范文对比：")
                        for i, comparison in enumerate(result.get('comparison_with_sample', []), 1):
                            feedback_parts.append(f"{i}. {comparison}")

                    # 添加高分技巧（新增）
                    if result.get('high_score_tips'):
                        feedback_parts.append("\n\n⭐ 提分建议：")
                        for i, tip in enumerate(result.get('high_score_tips', []), 1):
                            feedback_parts.append(f"{i}. {tip}")

                    detailed_feedback = "\n".join(feedback_parts)

                    logger.info(f"Writing scored: {score:.2f}, word_count: {word_count}")
                    return is_correct, score, detailed_feedback

                except Exception as llm_error:
                    logger.error(f"LLM writing scoring error: {llm_error}", exc_info=True)
                    # 降级到简单评分
                    if word_count < 100:
                        score = 0.5
                        feedback = f"字数偏少（{word_count}词），建议至少150词。LLM评分暂时不可用，已给予基础分。"
                        is_correct = False
                    else:
                        score = 0.7
                        feedback = f"字数达标（{word_count}词）。LLM评分暂时不可用，已给予基础分。"
                        is_correct = True
                    return is_correct, score, feedback

            except Exception as e:
                logger.error(f"Writing scoring error: {e}")
                return False, 0.5, "评分失败，已给予基础分"

        else:
            # 未知类型：默认字符串匹配
            is_correct = str(user_answer).strip() == str(correct_answer).strip()
            return is_correct, 1.0 if is_correct else 0.0, None

    @staticmethod
    def get_quiz_history(
        db: Session,
        user_id: int,
        practice_mode: Optional[str] = None,
        chapter_id: Optional[int] = None,
        section_id: Optional[int] = None,
        subsection_id: Optional[int] = None,
        limit: int = 10
    ) -> List[QuizRecord]:
        """
        获取练习历史

        Args:
            db: 数据库会话
            user_id: 用户ID
            practice_mode: 练习方式（可选：chapter/random/comprehensive）
            chapter_id: 章节ID（可选）
            section_id: 节ID（可选）
            subsection_id: 小节ID（可选）
            limit: 返回数量限制

        Returns:
            List[QuizRecord]: 练习记录列表
        """
        query = db.query(QuizRecord).filter(QuizRecord.user_id == user_id)

        if practice_mode:
            if practice_mode == 'chapter':
                # chapter mode includes both 'chapter' and 'subsection' records
                query = query.filter(QuizRecord.practice_mode.in_(['chapter', 'subsection']))
            else:
                query = query.filter(QuizRecord.practice_mode == practice_mode)

        if chapter_id:
            query = query.filter(QuizRecord.chapter_id == chapter_id)
            
        if section_id:
            query = query.filter(QuizRecord.section_id == section_id)
            
        if subsection_id:
            query = query.filter(QuizRecord.subsection_id == subsection_id)

        records = query.order_by(QuizRecord.created_at.desc()).limit(limit).all()

        return records

    @staticmethod
    def get_quiz_stats(db: Session, user_id: int, chapter_id: Optional[int] = None, practice_mode: Optional[str] = None) -> Dict[str, Any]:
        """
        获取练习统计

        Args:
            db: 数据库会话
            user_id: 用户ID
            chapter_id: 章节ID（可选）
            practice_mode: 练习方式（可选）

        Returns:
            Dict: 统计数据
        """
        # 基础查询条件
        base_filters = [QuizRecord.user_id == user_id]
        if chapter_id is not None:
            base_filters.append(QuizRecord.chapter_id == chapter_id)
        if practice_mode:
            base_filters.append(QuizRecord.practice_mode == practice_mode)
        
        # 总练习数
        total_count = db.query(QuizRecord).filter(*base_filters).count()

        # 已完成数
        completed_filters = base_filters + [QuizRecord.is_completed == 1]
        completed_count = db.query(QuizRecord).filter(*completed_filters).count()

        # 平均分数
        from sqlalchemy import func
        avg_score = db.query(func.avg(QuizRecord.score)).filter(*completed_filters).scalar() or 0

        # 平均正确率
        avg_accuracy = db.query(func.avg(QuizRecord.accuracy)).filter(*completed_filters).scalar() or 0
        
        # 总做题数 (Completed)
        total_questions = db.query(func.sum(QuizRecord.question_count)).filter(*completed_filters).scalar() or 0

        # 及格次数 (>= 60)
        passed_filters = completed_filters + [QuizRecord.score >= 60]
        passed_count = db.query(QuizRecord).filter(*passed_filters).count()

        # 最高分
        max_score = db.query(func.max(QuizRecord.score)).filter(*completed_filters).scalar() or 0

        result = {
            "total_count": total_count,
            "completed_count": completed_count,
            "avg_score": round(avg_score, 1),
            "avg_accuracy": round(avg_accuracy, 1),
            "total_questions": int(total_questions),
            "passed_count": passed_count,
            "max_score": round(max_score, 1),
            # For compatibility with frontend if needed
            "pass_rate": round((passed_count / completed_count * 100) if completed_count > 0 else 0, 1)
        }

        # 如果指定了章节，计算详细的章节得分情况
        if chapter_id is not None:
            from app.models.subsection import SubSection
            from app.models.section import Section
            
            # 获取该章节下的所有小节
            # Chapter -> Section -> SubSection
            subsections = db.query(SubSection).join(Section).filter(Section.chapter_id == chapter_id).all()
            
            chapter_breakdown = []
            total_chapter_score = 0.0
            total_chapter_weight = 0.0
            
            for sub in subsections:
                # 获取该小节的练习记录
                sub_records = db.query(QuizRecord).filter(
                    QuizRecord.user_id == user_id,
                    QuizRecord.subsection_id == sub.id,
                    QuizRecord.is_completed == 1
                ).all()
                
                sub_total_quizzes = len(sub_records)
                sub_total_questions = sum(r.question_count for r in sub_records)
                
                # 计算平均分
                if sub_total_quizzes > 0:
                    sub_total_score_sum = sum(r.score for r in sub_records)
                    sub_avg_score = sub_total_score_sum / sub_total_quizzes
                else:
                    sub_avg_score = 0.0
                
                # 获取考核指标
                weight = sub.weight if sub.weight is not None else 0.0
                min_questions = sub.min_questions if sub.min_questions is not None else 10
                passing_score = sub.passing_score if sub.passing_score is not None else 60.0
                
                # 计算加权及格分
                weighted_passing_score = passing_score * (weight / 100.0)
                
                # 累加总权重
                total_chapter_weight += weight
                
                # 计算最终得分
                # 如果做题数不足，得分为0
                if sub_total_questions < min_questions:
                    final_score = 0.0
                    status_msg = f"做题数不足 (需{min_questions}题)"
                else:
                    final_score = sub_avg_score * (weight / 100.0)
                    status_msg = "已达标"
                
                total_chapter_score += final_score
                
                chapter_breakdown.append({
                    "subsection_id": sub.id,
                    "subsection_title": sub.title,
                    "weight": weight,
                    "min_questions": min_questions,
                    "passing_score": passing_score,
                    "weighted_passing_score": round(weighted_passing_score, 1),
                    "total_questions": sub_total_questions,
                    "average_score": round(sub_avg_score, 1),
                    "final_score": round(final_score, 1),
                    "status_msg": status_msg
                })
            
            # 计算目标达成通过分（总权重的80%）
            target_score = total_chapter_weight * 0.8
            
            result["chapter_score_breakdown"] = chapter_breakdown
            result["total_chapter_score"] = round(total_chapter_score, 1)
            result["is_chapter_passed"] = total_chapter_score >= target_score
            result["target_score"] = round(target_score, 1)

        return result

    @staticmethod
    async def create_personalized_quiz(
        db: Session,
        user_id: int,
        chapter_id: int,
        quiz_type: str,
        question_count: int = 5
    ) -> QuizRecord:
        """
        创建个性化练习（基于薄弱知识点）

        优先针对用户的薄弱知识点生成题目

        Args:
            db: 数据库会话
            user_id: 用户ID
            chapter_id: 章节ID
            quiz_type: 练习类型
            question_count: 题目数量

        Returns:
            QuizRecord: 练习记录
        """
        from app.services.wrong_question_service import wrong_question_service

        # 获取薄弱知识点
        weak_points = wrong_question_service.get_weak_knowledge_points(
            db=db,
            user_id=user_id,
            chapter_id=chapter_id,
            top_k=3
        )

        if weak_points:
            # 提取知识点ID
            kp_ids = [wp['knowledge_point_id'] for wp in weak_points]
            logger.info(f"Creating personalized quiz for user {user_id}, weak points: {kp_ids}")

            # 针对薄弱知识点出题
            return await QuizService.create_quiz(
                db=db,
                user_id=user_id,
                chapter_id=chapter_id,
                quiz_type=quiz_type,
                question_count=question_count,
                knowledge_point_ids=kp_ids
            )
        else:
            # 没有薄弱点，创建常规练习
            logger.info(f"No weak points found for user {user_id}, creating regular quiz")
            return await QuizService.create_quiz(
                db=db,
                user_id=user_id,
                chapter_id=chapter_id,
                quiz_type=quiz_type,
                question_count=question_count
            )


# 创建全局实例
quiz_service = QuizService()
