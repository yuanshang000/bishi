"""
聊天历史模型

定义聊天记录数据表结构和关系
"""

from sqlalchemy import Column, Integer, String, Text, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from datetime import datetime

from app.core.database import Base


class ChatHistory(Base):
    """
    聊天历史模型

    存储学生与AI助手的对话记录
    """
    __tablename__ = "chat_histories"

    # 主键
    id = Column(Integer, primary_key=True, index=True, autoincrement=True, comment="记录ID")

    # 外键
    user_id = Column(
        Integer,
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
        comment="用户ID"
    )
    chapter_id = Column(
        Integer,
        ForeignKey("chapters.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
        comment="关联章节ID（可选）"
    )

    # 会话信息
    session_id = Column(
        String(100),
        nullable=False,
        index=True,
        comment="会话ID（用于关联同一次对话）"
    )

    # 消息内容
    user_message = Column(Text, nullable=False, comment="用户消息")
    assistant_message = Column(Text, nullable=False, comment="助手回复")

    # 消息角色
    message_role = Column(String(20), default="user", comment="消息角色（user/assistant）")

    # RAG信息
    retrieved_docs = Column(Text, nullable=True, comment="检索到的文档片段（JSON格式）")
    doc_count = Column(Integer, default=0, comment="检索文档数量")

    # 元数据
    chat_metadata = Column(Text, nullable=True, comment="其他元数据（JSON格式）")

    # 时间戳
    created_at = Column(
        DateTime,
        nullable=False,
        default=datetime.utcnow,
        index=True,
        comment="创建时间"
    )

    # 关系
    user = relationship("User", back_populates="chat_histories")
    chapter = relationship("Chapter", back_populates="chat_histories")

    def __repr__(self):
        return f"<ChatHistory(id={self.id}, user_id={self.user_id}, session_id='{self.session_id}')>"

    def to_dict(self):
        """转换为字典格式"""
        return {
            "id": self.id,
            "user_id": self.user_id,
            "chapter_id": self.chapter_id,
            "session_id": self.session_id,
            "user_message": self.user_message,
            "assistant_message": self.assistant_message,
            "message_role": self.message_role,
            "doc_count": self.doc_count,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }
