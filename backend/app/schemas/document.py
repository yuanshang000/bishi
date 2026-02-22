"""
文档相关的Pydantic模式
"""

from typing import Optional
from pydantic import BaseModel, Field
from datetime import datetime


class DocumentBase(BaseModel):
    """文档基础模式"""
    chapter_id: int = Field(..., description="所属章节ID")
    title: str = Field(..., min_length=1, max_length=200, description="文档标题")
    doc_type: str = Field(..., description="文档类型 (textbook/teaching_plan/exercise/reference/knowledge)")


class DocumentCreate(DocumentBase):
    """文档创建模式"""
    content: Optional[str] = Field(None, description="文档文本内容")


class DocumentUpload(BaseModel):
    """文档上传模式"""
    chapter_id: int = Field(..., description="所属章节ID")
    title: str = Field(..., min_length=1, max_length=200, description="文档标题")
    doc_type: str = Field(..., description="文档类型")


class DocumentUpdate(BaseModel):
    """文档更新模式"""
    title: Optional[str] = Field(None, min_length=1, max_length=200)
    doc_type: Optional[str] = None
    content: Optional[str] = None


class DocumentResponse(DocumentBase):
    """文档响应模式"""
    id: int
    file_path: Optional[str]
    file_name: Optional[str]
    file_size: int
    is_vectorized: bool
    vector_count: int
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True
