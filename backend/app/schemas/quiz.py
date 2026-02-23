"""
练习相关的Pydantic模式
"""

from typing import Optional, List, Any, Dict
from pydantic import BaseModel, Field, field_validator
from datetime import datetime
import json


class QuestionBase(BaseModel):
    """题目基础模式"""
    question_type: str = Field(..., description="题目类型")
    question_text: str = Field(..., description="题目内容")
    options: Optional[List[str]] = Field(None, description="选项列表（选择题）")
    correct_answer: Any = Field(..., description="正确答案")
    explanation: Optional[str] = Field(None, description="答案解析")


class QuizBase(BaseModel):
    """练习基础模式"""
    chapter_id: Optional[int] = Field(None, description="章节ID（章节练习时必填）")
    subsection_id: Optional[int] = Field(None, description="小目标ID（目标练习时必填）")
    practice_mode: str = Field("chapter", description="练习方式 (chapter=章节练习, subsection=小目标练习, random=随机练习, comprehensive=综合练习)")
    quiz_type: str = Field(..., description="练习类型 (choice/blank/translation等)")
    difficulty: str = Field("intermediate", description="难度等级 (easy/intermediate/hard)")


class QuizCreate(QuizBase):
    """练习创建模式"""
    question_count: int = Field(5, ge=1, le=20, description="题目数量")


class QuizCreateTargeted(QuizCreate):
    """针对性练习创建模式（指定知识点）"""
    knowledge_point_ids: Optional[List[str]] = Field(None, description="知识点ID列表")


class WordTrainingCreate(BaseModel):
    """单词训练创建模式"""
    subsection_id: int = Field(..., description="小目标ID")
    count: int = Field(10, ge=1, le=50, description="题目数量")
    practice_mode: Optional[str] = Field("subsection", description="练习模式")


class ComprehensiveQuizCreate(BaseModel):
    """综合训练创建模式"""
    section_id: int = Field(..., description="小节ID")
    difficulty: str = Field(..., description="难度 (初级/中级/高级)")
    count: int = Field(5, ge=1, le=20, description="题目数量")


class QuizSubmit(BaseModel):
    """练习提交模式"""
    quiz_id: int = Field(..., description="练习记录ID")
    user_answers: List[Any] = Field(..., description="用户答案列表")
    time_spent: Optional[int] = Field(None, description="用时（秒）")


class QuizResponse(QuizBase):
    """练习响应模式"""
    id: int
    user_id: int
    practice_mode: str
    question_count: int
    questions: Optional[List[Dict[str, Any]]]
    user_answers: Optional[List[Any]] = None
    correct_answers: Optional[List[Any]] = None
    results: Optional[List[Dict[str, Any]]] = None
    score: float
    accuracy: float
    time_spent: int
    is_completed: bool
    knowledge_point_ids: Optional[List[str]] = Field(None, description="关联知识点ID")
    source_documents: Optional[List[Dict[str, Any]]] = Field(default=[], description="出题使用的文档列表")
    source_chunks: Optional[List[Dict[str, Any]]] = Field(default=[], description="RAG检索使用的分块预览列表")
    rag_context: Optional[str] = Field(default="", description="传入AI的上下文文本（截断）")
    applied_rules: Optional[str] = Field(default=None, description="本次出题所使用的规则摘要（仅显示与当前选择相关）")
    started_at: Optional[datetime]
    completed_at: Optional[datetime]
    created_at: datetime

    @field_validator('questions', mode='before')
    @classmethod
    def parse_questions(cls, v):
        """解析 questions JSON 字符串"""
        if v is None:
            return None
        if isinstance(v, str):
            try:
                return json.loads(v)
            except (json.JSONDecodeError, ValueError):
                return None
        return v

    @field_validator('user_answers', mode='before')
    @classmethod
    def parse_user_answers(cls, v):
        """解析 user_answers JSON 字符串"""
        if v is None:
            return None
        if isinstance(v, str):
            try:
                return json.loads(v)
            except (json.JSONDecodeError, ValueError):
                return None
        return v

    @field_validator('correct_answers', mode='before')
    @classmethod
    def parse_correct_answers(cls, v):
        """解析 correct_answers JSON 字符串"""
        if v is None:
            return None
        if isinstance(v, str):
            try:
                return json.loads(v)
            except (json.JSONDecodeError, ValueError):
                return None
        return v

    @field_validator('results', mode='before')
    @classmethod
    def parse_results(cls, v):
        """解析 results JSON 字符串"""
        if v is None:
            return None
        if isinstance(v, str):
            try:
                return json.loads(v)
            except (json.JSONDecodeError, ValueError):
                return None
        return v

    @field_validator('knowledge_point_ids', mode='before')
    @classmethod
    def parse_knowledge_point_ids(cls, v):
        """解析 knowledge_point_ids JSON 字符串"""
        if v is None:
            return None
        if isinstance(v, str):
            try:
                return json.loads(v)
            except (json.JSONDecodeError, ValueError):
                return None
        return v

    class Config:
        from_attributes = True


class QuizResult(BaseModel):
    """练习结果模式"""
    score: float
    accuracy: float
    correct_count: int
    wrong_count: int
    total_count: int
    time_spent: int
    results: List[Dict[str, Any]]


class SubsectionStats(BaseModel):
    """小节练习统计"""
    subsection_id: int
    subsection_title: str
    weight: float
    passing_score: float
    
    total_quizzes: int
    total_questions: int
    average_score: float
    final_score: float
    
    passed_quizzes: int
    min_questions: int = 10
