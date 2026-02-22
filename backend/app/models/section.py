"""
小节模型

定义课程章节下的小节数据表结构和关系
"""

from sqlalchemy import Column, Integer, String, Text, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from datetime import datetime

from app.core.database import Base


class Section(Base):
    """
    小节模型 (Section)
    
    层级：Chapter -> Section -> SubSection
    """
    __tablename__ = "sections"

    # 主键
    id = Column(Integer, primary_key=True, index=True, autoincrement=True, comment="小节ID")

    # 外键
    chapter_id = Column(
        Integer,
        ForeignKey("chapters.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
        comment="所属章节ID"
    )

    # 基本信息
    title = Column(String(200), nullable=False, comment="小节标题")
    description = Column(Text, nullable=True, comment="小节描述")
    order = Column(Integer, default=0, comment="排序顺序")

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
    chapter = relationship("Chapter", back_populates="sections")
    subsections = relationship(
        "SubSection",
        back_populates="section",
        cascade="all, delete-orphan",
        order_by="SubSection.order"
    )

    def __repr__(self):
        return f"<Section(id={self.id}, title='{self.title}')>"
