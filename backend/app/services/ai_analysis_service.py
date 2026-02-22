"""
AI 学情分析服务

集成 MCP Server 提供的学生数据，进行智能分析
"""

import sys
import os
import json
import asyncio
from typing import Dict, List, Any
import logging
from sqlalchemy.orm import Session
from app.models.chapter import Chapter
from app.models.section import Section
from app.models.subsection import SubSection
from app.models.quiz import QuizRecord

# 添加 mcp_server 到 Python 路径
mcp_server_path = os.path.join(os.path.dirname(__file__), '../../mcp_server')
if mcp_server_path not in sys.path:
    sys.path.insert(0, mcp_server_path)

from server import fetch_learning_data, fetch_wrong_questions, fetch_weak_knowledge_points

logger = logging.getLogger(__name__)


class AIAnalysisService:
    """AI 学情分析服务"""

    async def get_goal_completion_status(self, db: Session, student_id: int) -> List[Dict[str, Any]]:
        """
        获取目标（小节）完成情况
        
        Args:
            db: 数据库会话
            student_id: 学生ID
            
        Returns:
            List: 章节-小节结构及完成情况
        """
        # 1. Fetch all chapters with sections and subsections
        chapters = db.query(Chapter).order_by(Chapter.chapter_number).all()
        
        # 2. Fetch all quiz records for this student
        records = db.query(QuizRecord).filter(
            QuizRecord.user_id == student_id,
            QuizRecord.is_completed == 1
        ).all()
        
        # 3. Aggregate stats by subsection_id
        subsection_stats = {}
        for r in records:
            if r.subsection_id:
                sid = r.subsection_id
                if sid not in subsection_stats:
                    subsection_stats[sid] = {"total_score": 0, "count": 0, "max_score": 0}
                
                subsection_stats[sid]["total_score"] += r.score
                subsection_stats[sid]["count"] += 1
                subsection_stats[sid]["max_score"] = max(subsection_stats[sid]["max_score"], r.score)
        
        # 4. Build hierarchy with stats
        result = []
        for chapter in chapters:
            chapter_data = {
                "id": chapter.id,
                "title": chapter.title,
                "chapter_number": chapter.chapter_number,
                "sections": []
            }
            # Sort sections by order
            sorted_sections = sorted(chapter.sections, key=lambda s: s.order or 0)
            
            for section in sorted_sections:
                section_data = {
                    "id": section.id,
                    "title": section.title,
                    "order": section.order,
                    "subsections": []
                }
                # Sort subsections by order
                sorted_subsections = sorted(section.subsections, key=lambda s: s.order or 0)
                
                for subsection in sorted_subsections:
                    stats = subsection_stats.get(subsection.id, {"total_score": 0, "count": 0, "max_score": 0})
                    # Score is typically 0-100 in QuizRecord based on previous code
                    # But QuizRecord.score is Float, default 0.0. 
                    # If it's percentage, it might be 85.5. If it's 0-1, it might be 0.855.
                    # In analyze_student_performance: question_score = result_item.get("score", 0.0) * 100
                    # Let's assume QuizRecord.score is the total score of the quiz.
                    # If the quiz has 5 questions, max score is 5? Or is it normalized to 100?
                    # In quiz_service.py: quiz_record.score = total_score (sum of question scores)
                    # And accuracy is 0-100.
                    # Let's use accuracy for "score" visualization if available, or normalize score.
                    # Actually, let's just use the `max_score` achieved if it's stored as percentage, 
                    # OR calculate average accuracy.
                    
                    # Let's re-examine QuizRecord.score in quiz_service.py.
                    # It seems score is sum of individual question scores.
                    # Ideally we want the "Grade" (0-100). 
                    # QuizRecord has `accuracy` field (0-100). Let's use that.
                    
                    pass
                
        # Let's rewrite the aggregation loop to use accuracy
        subsection_stats = {}
        for r in records:
            if r.subsection_id:
                sid = r.subsection_id
                if sid not in subsection_stats:
                    subsection_stats[sid] = {"total_accuracy": 0, "count": 0, "max_accuracy": 0}
                
                subsection_stats[sid]["total_accuracy"] += r.accuracy
                subsection_stats[sid]["count"] += 1
                subsection_stats[sid]["max_accuracy"] = max(subsection_stats[sid]["max_accuracy"], r.accuracy)

        # Continue building hierarchy
        result = []
        for chapter in chapters:
            chapter_data = {
                "id": chapter.id,
                "title": chapter.title,
                "chapter_number": chapter.chapter_number,
                "sections": []
            }
            sorted_sections = sorted(chapter.sections, key=lambda s: s.order or 0)
            
            for section in sorted_sections:
                section_data = {
                    "id": section.id,
                    "title": section.title,
                    "order": section.order,
                    "subsections": []
                }
                sorted_subsections = sorted(section.subsections, key=lambda s: s.order or 0)
                
                for subsection in sorted_subsections:
                    stats = subsection_stats.get(subsection.id, {"total_accuracy": 0, "count": 0, "max_accuracy": 0})
                    avg_accuracy = stats["total_accuracy"] / stats["count"] if stats["count"] > 0 else 0
                    
                    passing_score = subsection.passing_score or 60
                    # Use max accuracy as "current level" or average? User said "visualize completion status".
                    # Usually "highest score" determines if you passed.
                    current_score = stats["max_accuracy"]
                    is_passed = current_score >= passing_score
                    
                    subsection_data = {
                        "id": subsection.id,
                        "title": subsection.title,
                        "content": subsection.content,
                        "passing_score": passing_score,
                        "current_score": round(current_score, 1),
                        "average_score": round(avg_accuracy, 1),
                        "practice_count": stats["count"],
                        "is_passed": is_passed,
                        "weight": subsection.weight
                    }
                    section_data["subsections"].append(subsection_data)
                chapter_data["sections"].append(section_data)
            result.append(chapter_data)
            
        return result

    async def get_learning_data(self, student_id: int, limit: int = 20) -> Dict[str, Any]:
        """
        获取学生练习记录

        Args:
            student_id: 学生ID
            limit: 返回记录数量

        Returns:
            Dict: 包含练习记录的字典
        """
        try:
            result = await fetch_learning_data({
                "student_id": student_id,
                "limit": limit
            })
            return json.loads(result[0].text)
        except Exception as e:
            logger.error(f"Failed to fetch learning data: {e}")
            return {"total_records": 0, "records": []}

    async def get_weak_knowledge_points(self, student_id: int, top_k: int = 5) -> Dict[str, Any]:
        """
        获取学生薄弱知识点

        Args:
            student_id: 学生ID
            top_k: 返回前K个薄弱点

        Returns:
            Dict: 包含薄弱知识点的字典
        """
        try:
            result = await fetch_weak_knowledge_points({
                "student_id": student_id,
                "top_k": top_k
            })
            return json.loads(result[0].text)
        except Exception as e:
            logger.error(f"Failed to fetch weak points: {e}")
            return {"total_weak_points": 0, "weak_knowledge_points": []}

    async def get_wrong_questions(self, student_id: int, limit: int = 30, is_mastered: bool = False) -> Dict[str, Any]:
        """
        获取学生错题记录

        Args:
            student_id: 学生ID
            limit: 返回记录数量
            is_mastered: 是否只返回未掌握的错题

        Returns:
            Dict: 包含错题记录的字典
        """
        try:
            result = await fetch_wrong_questions({
                "student_id": student_id,
                "limit": limit,
                "is_mastered": is_mastered
            })
            return json.loads(result[0].text)
        except Exception as e:
            logger.error(f"Failed to fetch wrong questions: {e}")
            return {"total_wrong_questions": 0, "wrong_questions": []}

    async def analyze_student_performance(self, student_id: int) -> Dict[str, Any]:
        """
        综合分析学生学习表现

        Args:
            student_id: 学生ID

        Returns:
            Dict: 分析结果
        """
        # 获取数据
        learning_data = await self.get_learning_data(student_id, limit=50)  # 增加数据量
        weak_points_from_errors = await self.get_weak_knowledge_points(student_id, top_k=5)

        # 计算统计数据
        total_records = learning_data["total_records"]
        records = learning_data["records"]

        if total_records == 0:
            return {
                "status": "no_data",
                "message": "还没有练习记录",
                "suggestion": "建议先完成一些章节练习"
            }

        # 计算平均分和趋势
        scores = [r["score"] for r in records]
        avg_score = sum(scores) / len(scores)

        # 最近3次的平均分（趋势）
        recent_scores = scores[:min(3, len(scores))]
        recent_avg = sum(recent_scores) / len(recent_scores)

        # 判断趋势
        if len(scores) >= 3:
            if recent_avg > avg_score + 5:
                trend = "improving"
                trend_text = "📈 进步趋势明显！继续保持"
            elif recent_avg < avg_score - 5:
                trend = "declining"
                trend_text = "⚠️ 成绩有所下降，需要加强练习"
            else:
                trend = "stable"
                trend_text = "📊 成绩稳定"
        else:
            trend = "insufficient_data"
            trend_text = "📝 数据较少，继续练习以获得更准确的分析"

        # 🔥 新增：基于题目级别的薄弱点分析
        # 不再按quiz_record统计，而是按每道题目统计
        # 这样综合练习中的多种题型可以分别统计到各自的题型中
        quiz_type_stats = {}

        # 练习方式统计
        practice_mode_stats = {
            "chapter": {"total_questions": 0, "total_records": 0, "by_quiz_type": {}},
            "random": {"total_questions": 0, "total_records": 0, "by_quiz_type": {}},
            "comprehensive": {"total_questions": 0, "total_records": 0, "by_quiz_type": {}}
        }

        # 章节统计（仅用于章节练习）
        chapter_stats = {}

        logger.info(f"Starting to analyze {len(records)} quiz records")

        for r in records:
            # 解析题目列表和结果
            questions = r.get("questions", [])
            results = r.get("results", [])
            practice_mode = r.get("practice_mode", "chapter")
            chapter_id = r.get("chapter_id")

            logger.debug(f"Processing record: quiz_id={r.get('quiz_id')}, practice_mode={practice_mode}, questions_type={type(questions)}, questions_count={len(questions) if isinstance(questions, list) else 'N/A'}")

            # 如果questions是字符串，需要解析（兼容性处理）
            if isinstance(questions, str):
                try:
                    questions = json.loads(questions)
                    logger.debug(f"Parsed questions string to list, count={len(questions)}")
                except Exception as e:
                    logger.warning(f"Failed to parse questions: {e}")
                    questions = []

            # 如果results是字符串，需要解析（兼容性处理）
            if isinstance(results, str):
                try:
                    results = json.loads(results)
                    logger.debug(f"Parsed results string to list, count={len(results)}")
                except Exception as e:
                    logger.warning(f"Failed to parse results: {e}")
                    results = []

            # 确保questions和results是列表
            if not isinstance(questions, list):
                logger.warning(f"Questions is not a list: {type(questions)}")
                questions = []
            if not isinstance(results, list):
                logger.warning(f"Results is not a list: {type(results)}")
                results = []

            # 统计此次练习的记录数
            if practice_mode in practice_mode_stats:
                practice_mode_stats[practice_mode]["total_records"] += 1

            # 遍历每道题目
            for i, question in enumerate(questions):
                # 获取题目的quiz_type（优先使用question级别的）
                quiz_type = question.get('quiz_type')

                # 如果question没有quiz_type，使用record级别的（兼容旧数据）
                # 但排除"mixed"（综合练习的占位标记）
                if not quiz_type:
                    record_quiz_type = r.get("quiz_type")
                    if record_quiz_type and record_quiz_type != "mixed":
                        quiz_type = record_quiz_type
                    else:
                        continue  # 跳过无效题型

                # 跳过"mixed"题型（不参与统计）
                if quiz_type == "mixed":
                    continue

                # 初始化题型统计
                if quiz_type not in quiz_type_stats:
                    quiz_type_stats[quiz_type] = {
                        "total_questions": 0,  # 总题数
                        "correct_count": 0,    # 正确题数
                        "total_score": 0.0,    # 总得分
                        "scores": [],          # 所有题目的得分列表
                        "chapter_practice": {"questions": 0, "correct": 0, "total_score": 0.0, "scores": []},
                        "random_practice": {"questions": 0, "correct": 0, "total_score": 0.0, "scores": []},
                        "comprehensive_practice": {"questions": 0, "correct": 0, "total_score": 0.0, "scores": []}
                    }

                # 获取该题目的结果
                question_score = 0.0
                is_correct = False

                if i < len(results):
                    result_item = results[i]
                    is_correct = result_item.get("is_correct", False)
                    # score字段是0-1的浮点数，转换为百分制
                    question_score = result_item.get("score", 0.0) * 100

                # 统计总体数据
                quiz_type_stats[quiz_type]["total_questions"] += 1
                if is_correct:
                    quiz_type_stats[quiz_type]["correct_count"] += 1
                quiz_type_stats[quiz_type]["total_score"] += question_score
                quiz_type_stats[quiz_type]["scores"].append(question_score)

                # 按练习方式分别统计
                practice_key = f"{practice_mode}_practice"
                if practice_key in quiz_type_stats[quiz_type]:
                    quiz_type_stats[quiz_type][practice_key]["questions"] += 1
                    if is_correct:
                        quiz_type_stats[quiz_type][practice_key]["correct"] += 1
                    quiz_type_stats[quiz_type][practice_key]["total_score"] += question_score
                    quiz_type_stats[quiz_type][practice_key]["scores"].append(question_score)

                # 🔥 新增：练习方式统计（按题型）
                if practice_mode in practice_mode_stats:
                    practice_mode_stats[practice_mode]["total_questions"] += 1
                    if quiz_type not in practice_mode_stats[practice_mode]["by_quiz_type"]:
                        practice_mode_stats[practice_mode]["by_quiz_type"][quiz_type] = 0
                    practice_mode_stats[practice_mode]["by_quiz_type"][quiz_type] += 1

                # 🔥 新增：章节统计（仅章节练习）
                if practice_mode == "chapter" and chapter_id:
                    if chapter_id not in chapter_stats:
                        chapter_stats[chapter_id] = {
                            "total_questions": 0,
                            "by_quiz_type": {}
                        }
                    chapter_stats[chapter_id]["total_questions"] += 1
                    if quiz_type not in chapter_stats[chapter_id]["by_quiz_type"]:
                        chapter_stats[chapter_id]["by_quiz_type"][quiz_type] = 0
                    chapter_stats[chapter_id]["by_quiz_type"][quiz_type] += 1


        # 分析每种题型的表现，找出薄弱点
        weak_point_analysis = []

        # 输出统计结果日志
        logger.info(f"Analysis statistics summary:")
        logger.info(f"  - Practice mode stats: chapter={practice_mode_stats['chapter']['total_questions']}题, random={practice_mode_stats['random']['total_questions']}题, comprehensive={practice_mode_stats['comprehensive']['total_questions']}题")

        # 构建题型统计字符串（避免f-string嵌套引号问题）
        quiz_type_summary = ', '.join([
            f"{qt}={stats.get('total_questions', 0)}题"
            for qt, stats in quiz_type_stats.items()
            if qt != 'mixed' and stats.get('total_questions', 0) > 0
        ])
        logger.info(f"  - Quiz type stats: {quiz_type_summary}")
        logger.info(f"  - Chapter stats: {len(chapter_stats)} chapters")

        quiz_type_names = {
            "listening": "听力理解",
            "reading": "阅读理解",
            "translation": "翻译练习",
            "writing": "写作练习"
        }

        for quiz_type, stats in quiz_type_stats.items():
            # 跳过"mixed"题型
            if quiz_type == "mixed":
                continue

            if stats["total_questions"] == 0:
                continue

            # 计算平均分
            avg_score = stats["total_score"] / stats["total_questions"]

            # 计算正确率
            accuracy = (stats["correct_count"] / stats["total_questions"]) * 100

            # 计算各练习方式的详细统计
            practice_mode_details = {}
            for mode in ["chapter", "random", "comprehensive"]:
                practice_key = f"{mode}_practice"
                practice_data = stats[practice_key]
                if practice_data["questions"] > 0:
                    practice_mode_details[mode] = {
                        "questions": practice_data["questions"],
                        "correct": practice_data["correct"],
                        "accuracy": round((practice_data["correct"] / practice_data["questions"]) * 100, 1),
                        "avg_score": round(practice_data["total_score"] / practice_data["questions"], 1)
                    }

            # 判断是否为薄弱点：平均分低于70分或正确率低于70%
            if avg_score < 70 or accuracy < 70:
                # 计算严重程度
                severity_score = (avg_score + accuracy) / 2
                if severity_score < 40:
                    severity = "high"
                    severity_text = "严重"
                elif severity_score < 60:
                    severity = "medium"
                    severity_text = "中等"
                else:
                    severity = "low"
                    severity_text = "轻微"

                weak_point_analysis.append({
                    "knowledge_point_id": quiz_type_names.get(quiz_type, quiz_type),
                    "quiz_type": quiz_type,
                    "error_count": stats["total_questions"] - stats["correct_count"],  # 错题数
                    "total_questions": stats["total_questions"],
                    "correct_count": stats["correct_count"],
                    "accuracy": round(accuracy, 1),
                    "average_score": round(avg_score, 1),
                    "severity": severity,
                    "severity_text": severity_text,
                    "practice_mode_details": practice_mode_details,
                    "related_chapters": list(set([r.get("chapter_id") for r in records
                                                  if r.get("chapter_id") and
                                                  any(q.get("quiz_type") == quiz_type for q in (r.get("questions") or []))]))
                })

        # 按平均分从低到高排序（最薄弱的在前面）
        weak_point_analysis.sort(key=lambda x: x["average_score"])

        # 如果没有基于分数的薄弱点，再看基于错题的薄弱点
        if not weak_point_analysis and weak_points_from_errors["total_weak_points"] > 0:
            for wp in weak_points_from_errors["weak_knowledge_points"]:
                weak_point_analysis.append({
                    "knowledge_point_id": wp["knowledge_point_id"],
                    "quiz_type": None,
                    "error_count": wp["error_count"],
                    "average_score": None,
                    "severity": "high" if wp["error_count"] >= 5 else "medium" if wp["error_count"] >= 3 else "low",
                    "severity_text": "高" if wp["error_count"] >= 5 else "中" if wp["error_count"] >= 3 else "低",
                    "related_chapters": wp["related_chapters"]
                })

        return {
            "status": "success",
            "total_records": total_records,
            "average_score": round(avg_score, 2),
            "recent_average": round(recent_avg, 2),
            "trend": trend,
            "trend_text": trend_text,
            "weak_points": weak_point_analysis,
            "has_weak_points": len(weak_point_analysis) > 0,
            "quiz_type_stats": quiz_type_stats,  # 题型统计
            "practice_mode_stats": practice_mode_stats,  # 🔥 新增：练习方式统计
            "chapter_stats": chapter_stats  # 🔥 新增：章节统计
        }

    def generate_analysis_report(self, analysis: Dict[str, Any]) -> str:
        """
        生成人类可读的分析报告

        Args:
            analysis: 分析结果

        Returns:
            str: 分析报告文本
        """
        if analysis["status"] == "no_data":
            return analysis["message"]

        practice_mode_stats = analysis.get("practice_mode_stats", {})
        chapter_stats = analysis.get("chapter_stats", {})
        quiz_type_stats = analysis.get("quiz_type_stats", {})

        # 题型名称映射
        quiz_type_names = {
            "listening": "听力理解",
            "reading": "阅读理解",
            "translation": "翻译练习",
            "writing": "写作练习"
        }

        report = f"""📊 学习情况详细分析报告

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
【整体表现】
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

✅ 完成练习：{analysis['total_records']} 次
📝 平均分：{analysis['average_score']} 分
📈 最近表现：{analysis['recent_average']} 分
{analysis['trend_text']}

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
【练习方式统计】
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
"""

        # 1. 章节训练统计
        chapter_mode = practice_mode_stats.get("chapter", {})
        if chapter_mode.get("total_questions", 0) > 0:
            report += f"\n📚 章节训练：\n"
            report += f"   • 总题数：{chapter_mode['total_questions']} 题\n"
            report += f"   • 练习次数：{chapter_mode['total_records']} 次\n"

            if chapter_mode.get("by_quiz_type"):
                report += f"   • 题型分布：\n"
                for qtype, count in sorted(chapter_mode["by_quiz_type"].items(), key=lambda x: x[1], reverse=True):
                    type_name = quiz_type_names.get(qtype, qtype)
                    percentage = (count / chapter_mode['total_questions']) * 100
                    report += f"     - {type_name}：{count} 题 ({percentage:.1f}%)\n"

            # 章节详细统计
            if chapter_stats:
                report += f"\n   📖 各章节练习情况：\n"
                for chapter_id in sorted(chapter_stats.keys()):
                    ch_stat = chapter_stats[chapter_id]
                    report += f"     • 第 {chapter_id} 章：{ch_stat['total_questions']} 题\n"
                    for qtype, count in sorted(ch_stat["by_quiz_type"].items(), key=lambda x: x[1], reverse=True):
                        type_name = quiz_type_names.get(qtype, qtype)
                        report += f"       - {type_name}：{count} 题\n"
        else:
            report += f"\n📚 章节训练：尚未开始\n"

        # 2. 随机训练统计
        random_mode = practice_mode_stats.get("random", {})
        if random_mode.get("total_questions", 0) > 0:
            report += f"\n🎲 随机训练：\n"
            report += f"   • 总题数：{random_mode['total_questions']} 题\n"
            report += f"   • 练习次数：{random_mode['total_records']} 次\n"

            if random_mode.get("by_quiz_type"):
                report += f"   • 题型分布：\n"
                for qtype, count in sorted(random_mode["by_quiz_type"].items(), key=lambda x: x[1], reverse=True):
                    type_name = quiz_type_names.get(qtype, qtype)
                    percentage = (count / random_mode['total_questions']) * 100
                    report += f"     - {type_name}：{count} 题 ({percentage:.1f}%)\n"
        else:
            report += f"\n🎲 随机训练：尚未开始\n"

        # 3. 综合训练统计
        comprehensive_mode = practice_mode_stats.get("comprehensive", {})
        if comprehensive_mode.get("total_questions", 0) > 0:
            report += f"\n🎯 综合训练：\n"
            report += f"   • 总题数：{comprehensive_mode['total_questions']} 题\n"
            report += f"   • 练习次数：{comprehensive_mode['total_records']} 次\n"

            if comprehensive_mode.get("by_quiz_type"):
                report += f"   • 题型分布：\n"
                for qtype, count in sorted(comprehensive_mode["by_quiz_type"].items(), key=lambda x: x[1], reverse=True):
                    type_name = quiz_type_names.get(qtype, qtype)
                    percentage = (count / comprehensive_mode['total_questions']) * 100
                    report += f"     - {type_name}：{count} 题 ({percentage:.1f}%)\n"
        else:
            report += f"\n🎯 综合训练：尚未开始\n"

        # 4. 题型表现分析
        report += f"\n━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
        report += f"【题型表现分析】\n"
        report += f"━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"

        if quiz_type_stats:
            for qtype, stats in sorted(quiz_type_stats.items(), key=lambda x: x[1].get("average_score", 0) if x[1].get("total_questions", 0) > 0 else 0):
                if qtype == "mixed":
                    continue

                if stats["total_questions"] == 0:
                    continue

                type_name = quiz_type_names.get(qtype, qtype)
                avg_score = stats["total_score"] / stats["total_questions"]
                accuracy = (stats["correct_count"] / stats["total_questions"]) * 100

                # 评级
                if avg_score >= 80:
                    rating = "优秀 ⭐⭐⭐"
                    rating_color = "🟢"
                elif avg_score >= 70:
                    rating = "良好 ⭐⭐"
                    rating_color = "🟡"
                elif avg_score >= 60:
                    rating = "及格 ⭐"
                    rating_color = "🟠"
                else:
                    rating = "需提高"
                    rating_color = "🔴"

                report += f"\n{rating_color} {type_name}：\n"
                report += f"   • 总题数：{stats['total_questions']} 题\n"
                report += f"   • 平均分：{avg_score:.1f} 分\n"
                report += f"   • 正确率：{accuracy:.1f}%\n"
                report += f"   • 评级：{rating}\n"

                # 各练习方式的表现
                chapter_perf = stats["chapter_practice"]
                random_perf = stats["random_practice"]
                comp_perf = stats["comprehensive_practice"]

                if chapter_perf["questions"] > 0 or random_perf["questions"] > 0 or comp_perf["questions"] > 0:
                    report += f"   • 练习方式表现：\n"

                    if chapter_perf["questions"] > 0:
                        ch_avg = chapter_perf["total_score"] / chapter_perf["questions"]
                        ch_acc = (chapter_perf["correct"] / chapter_perf["questions"]) * 100
                        report += f"     - 章节训练：{chapter_perf['questions']}题，平均{ch_avg:.1f}分，正确率{ch_acc:.1f}%\n"

                    if random_perf["questions"] > 0:
                        rd_avg = random_perf["total_score"] / random_perf["questions"]
                        rd_acc = (random_perf["correct"] / random_perf["questions"]) * 100
                        report += f"     - 随机训练：{random_perf['questions']}题，平均{rd_avg:.1f}分，正确率{rd_acc:.1f}%\n"

                    if comp_perf["questions"] > 0:
                        cp_avg = comp_perf["total_score"] / comp_perf["questions"]
                        cp_acc = (comp_perf["correct"] / comp_perf["questions"]) * 100
                        report += f"     - 综合训练：{comp_perf['questions']}题，平均{cp_avg:.1f}分，正确率{cp_acc:.1f}%\n"
        else:
            report += "\n暂无题型数据\n"

        # 5. 薄弱环节分析
        report += f"\n━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
        report += f"【薄弱环节分析】\n"
        report += f"━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"

        if analysis["has_weak_points"]:
            for i, wp in enumerate(analysis["weak_points"][:5], 1):
                severity_emoji = "🔴" if wp["severity"] == "high" else "🟡" if wp["severity"] == "medium" else "🟢"

                if wp.get("average_score") is not None:
                    report += f"\n{i}. {severity_emoji} {wp['knowledge_point_id']} ({wp['severity_text']}薄弱)\n"
                    report += f"   • 平均分：{wp['average_score']} 分\n"
                    report += f"   • 正确率：{wp['accuracy']}%\n"
                    report += f"   • 练习题数：{wp['total_questions']} 题（其中错题 {wp['error_count']} 题）\n"
                else:
                    report += f"\n{i}. {severity_emoji} {wp['knowledge_point_id']} ({wp['severity_text']}薄弱)\n"
                    report += f"   • 错误次数：{wp['error_count']} 次\n"
        else:
            report += "\n🎉 表现优秀！没有明显的薄弱点，继续保持！\n"

        # 6. 综合分析与改进建议
        report += f"\n━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
        report += f"【综合分析与改进建议】\n"
        report += f"━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"

        # 整体分析
        total_questions = sum(mode.get("total_questions", 0) for mode in practice_mode_stats.values())

        report += f"\n📊 整体分析：\n"
        report += f"   • 你已累计练习 {total_questions} 道题目\n"

        if analysis['average_score'] >= 80:
            report += f"   • 整体水平优秀，保持良好的学习势头\n"
        elif analysis['average_score'] >= 70:
            report += f"   • 整体水平良好，还有提升空间\n"
        elif analysis['average_score'] >= 60:
            report += f"   • 整体水平及格，需要加强练习\n"
        else:
            report += f"   • 整体水平需要提高，建议系统性复习\n"

        # 学习趋势分析
        if analysis['trend'] == "improving":
            report += f"   • 学习趋势：近期表现呈上升趋势，说明学习方法有效\n"
        elif analysis['trend'] == "declining":
            report += f"   • 学习趋势：近期表现有所下滑，需要调整学习策略\n"
        else:
            report += f"   • 学习趋势：成绩较为稳定\n"

        # 练习方式建议
        report += f"\n💡 练习方式建议：\n"

        chapter_questions = practice_mode_stats.get("chapter", {}).get("total_questions", 0)
        random_questions = practice_mode_stats.get("random", {}).get("total_questions", 0)
        comp_questions = practice_mode_stats.get("comprehensive", {}).get("total_questions", 0)

        if chapter_questions == 0:
            report += f"   • 🔔 建议开始章节训练，系统学习各章节知识点\n"
        elif chapter_questions < total_questions * 0.5:
            report += f"   • 📚 建议增加章节训练比重，巩固基础知识\n"

        if random_questions == 0:
            report += f"   • 🔔 建议尝试随机训练，提高知识迁移能力\n"
        elif random_questions < total_questions * 0.2:
            report += f"   • 🎲 建议增加随机训练，培养灵活应变能力\n"

        if comp_questions == 0 and analysis["has_weak_points"]:
            report += f"   • 🔔 建议使用综合训练，针对薄弱点进行强化\n"

        # 针对薄弱点的具体建议
        if analysis["has_weak_points"]:
            report += f"\n🎯 针对性提升建议：\n"

            weakest = analysis["weak_points"][0]

            if weakest.get("average_score") is not None:
                if weakest["average_score"] < 40:
                    report += f"   • 🔴 {weakest['knowledge_point_id']}是你目前最薄弱的环节（平均{weakest['average_score']}分）\n"
                    report += f"      - 建议系统复习相关基础知识和语法规则\n"
                    report += f"      - 每天专项练习该题型10-15分钟\n"
                    report += f"      - 可以寻求老师或同学的帮助，讲解易错点\n"
                elif weakest["average_score"] < 60:
                    report += f"   • 🟡 {weakest['knowledge_point_id']}需要加强（平均{weakest['average_score']}分）\n"
                    report += f"      - 复习相关知识点，总结错题规律\n"
                    report += f"      - 增加该题型的练习量，目标提升到70分以上\n"
                else:
                    report += f"   • 🟢 {weakest['knowledge_point_id']}还有提升空间（平均{weakest['average_score']}分）\n"
                    report += f"      - 继续保持练习，争取突破80分\n"
                    report += f"      - 多做难度较高的题目，提升应试能力\n"

            # 多个薄弱点的建议
            if len(analysis["weak_points"]) > 1:
                report += f"\n   • 💪 其他需要关注的题型：\n"
                for wp in analysis["weak_points"][1:4]:  # 最多显示3个
                    if wp.get("average_score") is not None:
                        report += f"      - {wp['knowledge_point_id']}（平均{wp['average_score']}分）\n"

        # 学习习惯建议
        report += f"\n📈 学习习惯建议：\n"
        report += f"   • 保持每天练习的习惯，建议每天至少完成5-10题\n"
        report += f"   • 及时复习错题，建立错题本，定期回顾\n"
        report += f"   • 综合运用章节训练、随机训练和综合训练，全面提升\n"
        report += f"   • 设定阶段性目标，如每周提升5分，逐步突破\n"

        report += f"\n━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
        report += f"继续努力，祝你学习进步！💪\n"

        return report


# 创建全局实例
ai_analysis_service = AIAnalysisService()
