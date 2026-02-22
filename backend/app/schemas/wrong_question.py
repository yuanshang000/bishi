"""
错题相关的Pydantic模式
"""

from typing import Optional, List, Any, Dict
from pydantic import BaseModel, Field
from datetime import datetime


class WrongQuestionBase(BaseModel):
    """错题基础模式"""
    question_type: str = Field(..., description="题目类型")
    question_data: Dict[str, Any] = Field(..., description="题目内容")
    user_answer: Any = Field(None, description="用户答案")
    correct_answer: Any = Field(None, description="正确答案")
    score: float = Field(0.0, description="得分（0-1）")


class WrongQuestionResponse(WrongQuestionBase):
    """错题响应模式"""
    id: int
    user_id: int
    quiz_record_id: int
    chapter_id: int
    knowledge_point_ids: Optional[List[str]] = Field(None, description="关联知识点ID")
    is_mastered: bool = Field(False, description="是否已掌握")
    retry_count: int = Field(0, description="重做次数")
    last_retry_score: Optional[float] = Field(None, description="最后一次重做得分")
    last_retry_at: Optional[datetime] = Field(None, description="最后重做时间")
    created_at: datetime

    class Config:
        from_attributes = True


class WrongQuestionListParams(BaseModel):
    """错题列表查询参数"""
    chapter_id: Optional[int] = Field(None, description="章节ID")
    is_mastered: Optional[bool] = Field(None, description="是否已掌握")
    limit: int = Field(20, ge=1, le=100, description="返回数量")


class WeakKnowledgePoint(BaseModel):
    """薄弱知识点统计"""
    knowledge_point_id: str = Field(..., description="知识点ID")
    error_count: int = Field(..., description="错误次数")
    avg_score: float = Field(..., description="平均分")


class WeakKnowledgePointResponse(BaseModel):
    """薄弱知识点响应"""
    chapter_id: Optional[int] = Field(None, description="章节ID")
    weak_points: List[WeakKnowledgePoint] = Field(..., description="薄弱知识点列表")


class ReviewQuizCreate(BaseModel):
    """错题重练创建模式"""
    chapter_id: Optional[int] = Field(None, description="章节ID（可选）")
    question_count: int = Field(5, ge=1, le=20, description="题目数量")


class ReviewQuizResponse(BaseModel):
    """错题重练响应"""
    questions: List[Dict[str, Any]] = Field(..., description="题目列表")
    wrong_question_ids: List[int] = Field(..., description="错题ID列表")


class MasteryUpdate(BaseModel):
    """掌握状态更新"""
    is_mastered: bool = Field(..., description="是否已掌握")
    retry_score: Optional[float] = Field(None, description="重做得分")


class WrongQuestionStats(BaseModel):
    """错题统计"""
    total_count: int = Field(..., description="总错题数")
    unmastered_count: int = Field(..., description="未掌握数")
    mastered_count: int = Field(..., description="已掌握数")
    mastery_rate: float = Field(..., description="掌握率（百分比）")


class KnowledgePoint(BaseModel):
    """知识点模式"""
    id: str = Field(..., description="知识点ID")
    name: str = Field(..., description="知识点名称")
    category: str = Field(..., description="分类")
    description: Optional[str] = Field(None, description="描述")
    examples: Optional[List[str]] = Field(None, description="示例列表")


class KnowledgePointsResponse(BaseModel):
    """知识点列表响应"""
    chapter_id: int = Field(..., description="章节ID")
    knowledge_points: List[KnowledgePoint] = Field(..., description="知识点列表")
