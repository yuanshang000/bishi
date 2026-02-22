"""
聊天相关的Pydantic模式
"""

from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field
from datetime import datetime


class ChatMessage(BaseModel):
    """聊天消息模式"""
    role: str = Field(..., description="角色 (user/assistant)")
    content: str = Field(..., description="消息内容")


class ChatBase(BaseModel):
    """聊天基础模式"""
    session_id: str = Field(..., description="会话ID")
    user_message: str = Field(..., min_length=1, description="用户消息")


class ChatRequest(BaseModel):
    """聊天请求模式"""
    message: str = Field(..., min_length=1, description="用户消息")
    chapter_id: Optional[int] = Field(None, description="章节ID（可选）")
    session_id: Optional[str] = Field(None, description="会话ID（可选）")
    use_rag: bool = Field(True, description="是否使用RAG检索")
    image: Optional[str] = Field(None, description="图片base64数据（可选）")
    mode: Optional[str] = Field("chat", description="模式 (chat/quiz)")


class ChatCreate(ChatBase):
    """聊天创建模式"""
    chapter_id: Optional[int] = None
    assistant_message: str = Field(..., description="助手回复")
    retrieved_docs: Optional[List[Dict[str, Any]]] = None
    doc_count: int = 0


class ChatResponse(ChatBase):
    """聊天响应模式"""
    id: int
    user_id: int
    chapter_id: Optional[int]
    assistant_message: str
    message_role: str
    doc_count: int
    created_at: datetime

    class Config:
        from_attributes = True


class ChatHistoryResponse(BaseModel):
    """聊天历史响应模式"""
    session_id: str
    messages: List[ChatMessage]
    chapter_id: Optional[int] = None
    created_at: datetime
