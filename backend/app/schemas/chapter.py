"""
章节相关的Pydantic模式
"""

from typing import Optional, List
from pydantic import BaseModel, Field, field_validator
from datetime import datetime
from app.schemas.section import SectionResponse


class ChapterBase(BaseModel):
    """章节基础模式"""
    chapter_number: int = Field(..., ge=1, description="章节编号")
    title: str = Field(..., min_length=1, max_length=200, description="章节标题")
    description: Optional[str] = Field(None, description="章节描述")
    learning_objectives: Optional[List[str]] = Field(None, description="学习目标列表")
    key_points: Optional[List[str]] = Field(None, description="知识点列表")
    word_count: Optional[int] = Field(0, ge=0, description="词汇量")
    difficulty_level: Optional[str] = Field("intermediate", description="难度等级")


class ChapterCreate(ChapterBase):
    """章节创建模式"""
    pass


class ChapterUpdate(BaseModel):
    """章节更新模式"""
    title: Optional[str] = Field(None, min_length=1, max_length=200)
    description: Optional[str] = None
    learning_objectives: Optional[List[str]] = None
    key_points: Optional[List[str]] = None
    word_count: Optional[int] = Field(None, ge=0)
    difficulty_level: Optional[str] = None


class ChapterResponse(ChapterBase):
    """章节响应模式"""
    id: int
    created_at: datetime
    updated_at: datetime
    sections: List[SectionResponse] = []

    class Config:
        from_attributes = True

    @field_validator('learning_objectives', mode='before')
    @classmethod
    def parse_learning_objectives(cls, v):
        if v is None:
            return None
        if isinstance(v, str):
            try:
                import json
                data = json.loads(v)
                return data if isinstance(data, list) else None
            except Exception:
                return None
        return v

    @field_validator('key_points', mode='before')
    @classmethod
    def parse_key_points(cls, v):
        if v is None:
            return None
        if isinstance(v, str):
            try:
                import json
                data = json.loads(v)
                return data if isinstance(data, list) else None
            except Exception:
                return None
        return v
