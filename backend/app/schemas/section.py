from typing import Optional, List
from pydantic import BaseModel, Field
from app.schemas.subsection import SubSectionResponse

class SectionBase(BaseModel):
    title: str = Field(..., description="小节标题")
    order: Optional[int] = Field(0, description="排序")

class SectionCreate(SectionBase):
    chapter_id: int

class SectionUpdate(BaseModel):
    title: Optional[str] = None
    order: Optional[int] = None

class SectionResponse(SectionBase):
    id: int
    chapter_id: int
    subsections: List[SubSectionResponse] = []

    class Config:
        from_attributes = True
