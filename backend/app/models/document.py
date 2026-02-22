"""
课程文档模型

定义课程文档数据表结构和关系
"""

from sqlalchemy import Column, Integer, String, Text, DateTime, ForeignKey, Enum as SQLEnum
from sqlalchemy.orm import relationship
from sqlalchemy.dialects.mysql import LONGTEXT
from datetime import datetime
import enum

from app.core.database import Base


class DocumentType(str, enum.Enum):
    """文档类型枚举"""
    textbook = "textbook"      # 教材
    teaching_plan = "teaching_plan"  # 教案
    exercise = "exercise"      # 练习
    reference = "reference"    # 参考资料
    knowledge = "knowledge"    # 知识点文档


class CourseDocument(Base):
    """
    课程文档模型

    存储课程相关文档和元数据
    """
    __tablename__ = "course_documents"

    # 主键
    id = Column(Integer, primary_key=True, index=True, autoincrement=True, comment="文档ID")

    # 外键
    chapter_id = Column(
        Integer,
        ForeignKey("chapters.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
        comment="所属章节ID"
    )

    # 文档信息
    title = Column(String(200), nullable=False, comment="文档标题")
    doc_type = Column(
        SQLEnum(DocumentType),
        nullable=False,
        index=True,
        comment="文档类型"
    )
    file_path = Column(String(500), nullable=True, comment="文件路径")
    file_name = Column(String(200), nullable=True, comment="原始文件名")
    file_size = Column(Integer, default=0, comment="文件大小（字节）")

    # 文档内容
    content = Column(LONGTEXT, nullable=True, comment="文档文本内容（支持大文件）")
    content_hash = Column(String(64), nullable=True, index=True, comment="内容哈希（用于去重）")

    # 向量化信息
    is_vectorized = Column(Integer, default=0, comment="是否已向量化（1=是，0=否）")
    vector_count = Column(Integer, default=0, comment="向量数量")
    chroma_ids = Column(Text, nullable=True, comment="ChromaDB中的ID列表（JSON格式）")

    # 知识点信息
    knowledge_points = Column(
        Text,
        nullable=True,
        comment="提取的知识点列表（JSON格式）"
    )
    knowledge_tags = Column(
        Text,
        nullable=True,
        comment="知识点标签（JSON数组）"
    )

    # 元数据
    doc_metadata = Column(Text, nullable=True, comment="其他元数据（JSON格式）")

    # 时间戳
    created_at = Column(
        DateTime,
        nullable=False,
        default=datetime.utcnow,
        comment="创建时间"
    )
    updated_at = Column(
        DateTime,
        nullable=False,
        default=datetime.utcnow,
        onupdate=datetime.utcnow,
        comment="更新时间"
    )

    # 关系
    chapter = relationship("Chapter", back_populates="documents")

    def __repr__(self):
        return f"<CourseDocument(id={self.id}, title='{self.title}', type='{self.doc_type}')>"

    def to_dict(self):
        """转换为字典格式"""
        return {
            "id": self.id,
            "chapter_id": self.chapter_id,
            "title": self.title,
            "doc_type": self.doc_type.value,
            "file_path": self.file_path,
            "file_name": self.file_name,
            "file_size": self.file_size,
            "is_vectorized": bool(self.is_vectorized),
            "vector_count": self.vector_count,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }
