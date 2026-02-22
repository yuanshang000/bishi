from typing import Optional
from pydantic import BaseModel, Field

class SubSectionBase(BaseModel):
    title: str = Field(..., description="小目标标题")
    description: Optional[str] = Field(None, description="目标描述")
    content: Optional[str] = Field(None, description="内容")
    requirements: Optional[str] = Field(None, description="要求(JSON)")
    user_friendly_requirements: Optional[str] = Field(None, description="用户友好要求")
    weight: Optional[float] = Field(0.0, description="权重")
    passing_score: Optional[float] = Field(60.0, description="合格分数")
    min_questions: Optional[int] = Field(10, description="最少题量")
    order: Optional[int] = Field(0, description="排序")

class SubSectionCreate(SubSectionBase):
    section_id: int

class SubSectionUpdate(BaseModel):
    title: Optional[str] = None
    content: Optional[str] = None
    requirements: Optional[str] = None
    user_friendly_requirements: Optional[str] = None
    weight: Optional[float] = None
    passing_score: Optional[float] = None
    min_questions: Optional[int] = None
    order: Optional[int] = None

class SubSectionResponse(SubSectionBase):
    id: int
    section_id: int

    class Config:
        from_attributes = True
