"""
认证相关API路由
"""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.schemas.user import UserCreate, UserLogin, UserResponse, Token
from app.services.auth_service import AuthService
from app.api.dependencies import get_db, get_current_active_user
from app.models.user import User

router = APIRouter(prefix="/auth", tags=["认证"])


@router.post("/register", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
def register(
    user_data: UserCreate,
    db: Session = Depends(get_db)
):
    """
    用户注册

    - **username**: 用户名（3-50字符）
    - **password**: 密码（6-50字符）
    - **email**: 邮箱（可选）
    - **full_name**: 真实姓名（可选）
    - **role**: 角色，可选值: teacher, student（默认: student）
    """
    user = AuthService.register(db, user_data)
    return user


@router.post("/login", response_model=Token)
def login(
    login_data: UserLogin,
    db: Session = Depends(get_db)
):
    """
    用户登录

    - **username**: 用户名
    - **password**: 密码

    返回JWT访问令牌和刷新令牌
    """
    token = AuthService.login(db, login_data)
    return token


@router.post("/refresh", response_model=Token)
def refresh_token(
    refresh_token: str,
    db: Session = Depends(get_db)
):
    """
    刷新访问令牌

    - **refresh_token**: 刷新令牌

    返回新的访问令牌
    """
    token = AuthService.refresh_access_token(db, refresh_token)
    return token


@router.get("/me", response_model=UserResponse)
def get_current_user_info(
    current_user: User = Depends(get_current_active_user)
):
    """
    获取当前用户信息

    需要认证
    """
    return current_user


@router.get("/users/{user_id}", response_model=UserResponse)
def get_user_by_id(
    user_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """
    根据ID获取用户信息

    需要认证
    """
    user = AuthService.get_user_by_id(db, user_id)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="用户不存在"
        )
    return user


@router.get("/dashboard/stats", response_model=dict)
def get_dashboard_stats(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """
    获取教师仪表盘统计数据 (增强版)
    """
    if current_user.role == "teacher":
        from app.models.quiz import QuizRecord
        from app.models.chat import ChatHistory
        from app.models.document import CourseDocument
        from app.models.chapter import Chapter
        from app.models.wrong_question import WrongQuestion
        from app.models.knowledge_point import KnowledgePoint
        from app.models.user_knowledge_stats import UserKnowledgePointStats
        from app.models.custom_quiz import CustomQuizRecord
        from datetime import datetime, timedelta
        from sqlalchemy import func, desc, distinct
        
        # === 1. 核心指标 (Key Metrics) ===
        
        # 1.1 学生总数
        total_students = db.query(User).filter(User.role == "student").count()
        
        # 1.2 总刷题量 & 平均正确率
        total_quizzes = db.query(QuizRecord).count()
        avg_accuracy = db.query(func.avg(QuizRecord.accuracy)).filter(QuizRecord.is_completed == 1).scalar() or 0
        
        # 1.3 AI 辅导交互数
        total_ai_interactions = db.query(ChatHistory).count()
        
        # 1.4 AI 出题使用次数 (AI Quiz Generation Count)
        # 仅统计智能问答模式生成的题目 (CustomQuizRecord)
        total_ai_quiz_count = db.query(CustomQuizRecord).count()
        
        # === 2. 可视化图表数据 (Visual Analytics) ===
        
        # 2.1 全班章节掌握度 (Chapter Mastery)
        # Group by Chapter -> Avg Accuracy (仅统计学生)
        chapter_mastery = db.query(
            Chapter.title,
            Chapter.chapter_number,
            func.avg(QuizRecord.accuracy).label("avg_acc")
        ).join(QuizRecord, QuizRecord.chapter_id == Chapter.id)\
         .join(User, QuizRecord.user_id == User.id)\
         .filter(QuizRecord.is_completed == 1, User.role == "student")\
         .group_by(Chapter.id, Chapter.title, Chapter.chapter_number)\
         .order_by(Chapter.chapter_number)\
         .all()
         
        chapter_mastery_data = [
            {"name": f"章节{item.chapter_number}", "full_name": item.title, "value": round(item.avg_acc or 0, 1)}
            for i, item in enumerate(chapter_mastery)
        ]
        
        # 2.2 学情趋势 (Learning Trend) - Last 7 Days (仅统计学生)
        trend_data = []
        for i in range(6, -1, -1):
            day_start = datetime.utcnow().date() - timedelta(days=i)
            day_end = day_start + timedelta(days=1)
            
            # Daily Average Score
            daily_score = db.query(func.avg(QuizRecord.accuracy)).join(User).filter(
                QuizRecord.created_at >= day_start,
                QuizRecord.created_at < day_end,
                QuizRecord.is_completed == 1,
                User.role == "student"
            ).scalar() or 0
            
            # Daily Quiz Count
            daily_count = db.query(QuizRecord).join(User).filter(
                QuizRecord.created_at >= day_start,
                QuizRecord.created_at < day_end,
                User.role == "student"
            ).count()
            
            trend_data.append({
                "date": day_start.strftime("%m-%d"),
                "score": round(daily_score, 1),
                "count": daily_count
            })
            
        # 2.3 题型能力雷达 (Ability Radar) & 题型表现详情 (仅统计学生)
        # 统计维度：
        # 1. 单词 (word_training)
        # 2. 语法 (grammar)
        # 3. 综合 (practice_mode="random")
        
        # 基础查询：学生且已完成
        base_query = db.query(
            QuizRecord.quiz_type,
            QuizRecord.practice_mode,
            QuizRecord.accuracy,
            QuizRecord.id
        ).join(User, QuizRecord.user_id == User.id)\
         .filter(QuizRecord.is_completed == 1, User.role == "student")
         
        records = base_query.all()
        
        # 手动聚合
        stats = {
            "单词": {"total_acc": 0, "count": 0},
            "语法": {"total_acc": 0, "count": 0},
            "综合": {"total_acc": 0, "count": 0}
        }
        
        for r in records:
            key = None
            # 判断逻辑
            if r.practice_mode == "random":
                key = "综合"
            elif r.quiz_type == "word_training":
                key = "单词"
            elif r.quiz_type == "grammar":
                key = "语法"
            
            if key:
                stats[key]["total_acc"] += r.accuracy
                stats[key]["count"] += 1
                
        formatted_radar = []
        type_stats_list = []
        
        # 构建雷达图和列表数据
        for key in ["单词", "语法", "综合"]:
            data = stats[key]
            avg_acc = 0
            if data["count"] > 0:
                avg_acc = round(data["total_acc"] / data["count"], 1)
                
            formatted_radar.append({"name": key, "value": avg_acc})
            type_stats_list.append({
                "type": key,
                "accuracy": avg_acc,
                "count": data["count"]
            })
    
        # Sort table data by accuracy ascending (weakest first)
        type_stats_list.sort(key=lambda x: x["accuracy"])
    
        # === 3. 详细数据 (Detailed Insights) ===
        
        # 3.1 全班高频错题知识点 (Top Weaknesses)
        # 聚合 UserKnowledgePointStats，找出全班错误次数最多的知识点
        from app.models.subsection import SubSection
        from app.models.section import Section
        
        weak_points = db.query(
            KnowledgePoint.content,
            SubSection.title.label("subsection_title"),
            Section.title.label("section_title"),
            func.sum(UserKnowledgePointStats.total_attempts).label("total"),
            func.sum(UserKnowledgePointStats.correct_attempts).label("correct")
        ).join(UserKnowledgePointStats, UserKnowledgePointStats.knowledge_point_id == KnowledgePoint.id)\
         .join(SubSection, KnowledgePoint.subsection_id == SubSection.id)\
         .join(Section, SubSection.section_id == Section.id)\
         .join(User, UserKnowledgePointStats.user_id == User.id)\
         .filter(User.role == "student")\
         .group_by(KnowledgePoint.id, KnowledgePoint.content, SubSection.title, Section.title)\
         .having(func.sum(UserKnowledgePointStats.total_attempts) > 0)\
         .all()
         
        # Calculate error rate and sort by error count (total - correct)
        weak_points_list = []
        for content, sub_title, sec_title, total, correct in weak_points:
            error_count = total - correct
            if error_count > 0:
                error_rate = error_count / total
                weak_points_list.append({
                    "content": content,
                    "source": f"{sec_title} - {sub_title}",
                    "error_rate": round(error_rate * 100, 1),
                    "error_count": int(error_count),
                    "total_attempts": int(total)
                })
                
        # Sort by error count desc, take top 10
        weak_points_list.sort(key=lambda x: x["error_count"], reverse=True)
        top_weaknesses = weak_points_list[:10]
    
        return {
            "metrics": {
                "total_students": total_students,
                "total_quizzes": total_quizzes,
                "avg_accuracy": round(avg_accuracy, 1),
                "ai_interactions": total_ai_interactions,
                "ai_quiz_count": total_ai_quiz_count
            },
            "charts": {
                "chapter_mastery": chapter_mastery_data,
                "learning_trend": trend_data,
                "radar": formatted_radar
            },
            "details": {
                "weaknesses": top_weaknesses
            }
        }
        
    else:
        # === 学生端数据 (Student Dashboard) ===
        from app.models.quiz import QuizRecord
        from app.models.chat import ChatHistory
        from app.models.user_knowledge_stats import UserKnowledgePointStats
        from app.models.wrong_question import WrongQuestion
        from app.models.knowledge_point import KnowledgePoint
        from app.models.subsection import SubSection
        from app.models.section import Section
        from datetime import datetime, timedelta
        from sqlalchemy import func, desc, distinct
        
        # 1. 个人核心指标
        
        # 1.1 学习天数 (Active Days)
        # 统计 Quiz 和 Chat 的不同日期数
        quiz_days = db.query(func.date(QuizRecord.created_at)).filter(QuizRecord.user_id == current_user.id).distinct().all()
        chat_days = db.query(func.date(ChatHistory.created_at)).filter(ChatHistory.user_id == current_user.id).distinct().all()
        active_days_set = set([d[0] for d in quiz_days] + [d[0] for d in chat_days])
        learning_days = len(active_days_set)
        
        # 1.2 刷题总数 (Total Questions)
        total_questions = db.query(func.sum(QuizRecord.question_count)).filter(
            QuizRecord.user_id == current_user.id,
            QuizRecord.is_completed == 1
        ).scalar() or 0
        
        # 1.3 平均正确率 (Avg Accuracy)
        avg_accuracy = db.query(func.avg(QuizRecord.accuracy)).filter(
            QuizRecord.user_id == current_user.id,
            QuizRecord.is_completed == 1
        ).scalar() or 0
        
        # 1.4 待复习错题 (Pending Wrong Questions)
        pending_wrong_count = db.query(WrongQuestion).filter(
            WrongQuestion.user_id == current_user.id,
            WrongQuestion.is_mastered == 0
        ).count()
        
        # 2. 个人图表数据
        
        # 2.1 学习趋势 (Learning Trend) - Last 7 Days
        trend_data = []
        for i in range(6, -1, -1):
            day_start = datetime.utcnow().date() - timedelta(days=i)
            day_end = day_start + timedelta(days=1)
            
            daily_score = db.query(func.avg(QuizRecord.accuracy)).filter(
                QuizRecord.user_id == current_user.id,
                QuizRecord.created_at >= day_start,
                QuizRecord.created_at < day_end,
                QuizRecord.is_completed == 1
            ).scalar() or 0
            
            daily_count = db.query(func.sum(QuizRecord.question_count)).filter(
                QuizRecord.user_id == current_user.id,
                QuizRecord.created_at >= day_start,
                QuizRecord.created_at < day_end,
                QuizRecord.is_completed == 1
            ).scalar() or 0
            
            trend_data.append({
                "date": day_start.strftime("%m-%d"),
                "score": round(daily_score, 1),
                "count": int(daily_count)
            })
            
        # 2.2 个人能力模型 (Ability Radar)
        base_query = db.query(
            QuizRecord.quiz_type,
            QuizRecord.practice_mode,
            QuizRecord.accuracy
        ).filter(
            QuizRecord.user_id == current_user.id,
            QuizRecord.is_completed == 1
        )
        
        records = base_query.all()
        
        stats = {
            "单词": {"total_acc": 0, "count": 0},
            "语法": {"total_acc": 0, "count": 0},
            "综合": {"total_acc": 0, "count": 0}
        }
        
        for r in records:
            key = None
            if r.practice_mode == "random":
                key = "综合"
            elif r.quiz_type == "word_training":
                key = "单词"
            elif r.quiz_type == "grammar":
                key = "语法"
            
            if key:
                stats[key]["total_acc"] += r.accuracy
                stats[key]["count"] += 1
                
        formatted_radar = []
        for key in ["单词", "语法", "综合"]:
            data = stats[key]
            avg_acc = 0
            if data["count"] > 0:
                avg_acc = round(data["total_acc"] / data["count"], 1)
            formatted_radar.append({"name": key, "value": avg_acc})
            
        # 3. 推荐与列表
        
        # 3.1 待强化知识点 (Top Weaknesses)
        weak_points = db.query(
            KnowledgePoint.content,
            SubSection.title.label("subsection_title"),
            Section.title.label("section_title"),
            UserKnowledgePointStats.total_attempts,
            UserKnowledgePointStats.correct_attempts
        ).join(UserKnowledgePointStats, UserKnowledgePointStats.knowledge_point_id == KnowledgePoint.id)\
         .join(SubSection, KnowledgePoint.subsection_id == SubSection.id)\
         .join(Section, SubSection.section_id == Section.id)\
         .filter(
             UserKnowledgePointStats.user_id == current_user.id,
             UserKnowledgePointStats.total_attempts > 0
         ).all()
         
        weak_points_list = []
        for content, sub_title, sec_title, total, correct in weak_points:
            error_count = total - correct
            if error_count > 0:
                error_rate = error_count / total
                weak_points_list.append({
                    "content": content,
                    "source": f"{sec_title} - {sub_title}",
                    "error_rate": round(error_rate * 100, 1),
                    "error_count": int(error_count)
                })
        
        weak_points_list.sort(key=lambda x: x["error_count"], reverse=True)
        top_weaknesses = weak_points_list[:5]
        
        # 3.2 最近练习记录
        recent_quizzes = db.query(
            QuizRecord.created_at,
            QuizRecord.quiz_type,
            QuizRecord.practice_mode,
            QuizRecord.score,
            QuizRecord.accuracy,
            QuizRecord.question_count
        ).filter(
            QuizRecord.user_id == current_user.id,
            QuizRecord.is_completed == 1
        ).order_by(desc(QuizRecord.created_at)).limit(5).all()
        
        activities = []
        for q in recent_quizzes:
            q_type_name = "未知"
            if q.practice_mode == "random":
                q_type_name = "综合训练"
            elif q.quiz_type == "word_training":
                q_type_name = "单词训练"
            elif q.quiz_type == "grammar":
                q_type_name = "语法训练"
            else:
                q_type_name = "章节练习"
                
            activities.append({
                "time": q.created_at.strftime("%Y-%m-%d %H:%M"),
                "content": f"完成了 {q_type_name} ({q.question_count}题)",
                "score": round(q.accuracy, 1) # 显示正确率更直观
            })
            
        return {
            "metrics": {
                "learning_days": learning_days,
                "total_questions": int(total_questions),
                "avg_accuracy": round(avg_accuracy, 1),
                "pending_wrong": pending_wrong_count
            },
            "charts": {
                "trend": trend_data,
                "radar": formatted_radar
            },
            "details": {
                "weaknesses": top_weaknesses,
                "recent_activities": activities
            }
        }
