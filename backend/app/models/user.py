"""
用户模型

定义用户数据表结构和关系
"""

from sqlalchemy import Column, Integer, String, Enum as SQLEnum, DateTime
from sqlalchemy.orm import relationship
from datetime import datetime
import enum

from app.core.database import Base


class UserRole(str, enum.Enum):
    """用户角色枚举"""
    teacher = "teacher"  # 教师
    student = "student"  # 学生


class User(Base):
    """
    用户模型

    存储用户基本信息、认证信息和角色
    """
    __tablename__ = "users"

    # 主键
    id = Column(Integer, primary_key=True, index=True, autoincrement=True, comment="用户ID")

    # 基本信息
    username = Column(
        String(50),
        unique=True,
        nullable=False,
        index=True,
        comment="用户名（唯一）"
    )
    email = Column(
        String(100),
        unique=True,
        nullable=True,
        index=True,
        comment="电子邮箱"
    )
    full_name = Column(String(100), nullable=True, comment="真实姓名")

    # 认证信息
    password_hash = Column(String(255), nullable=False, comment="密码哈希值")

    # 角色权限
    role = Column(
        SQLEnum(UserRole, native_enum=False),
        nullable=False,
        default=UserRole.student,
        index=True,
        comment="用户角色"
    )

    # 状态信息
    is_active = Column(Integer, default=1, comment="账号状态（1=启用，0=禁用）")

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
    quiz_records = relationship(
        "QuizRecord",
        back_populates="user",
        cascade="all, delete-orphan",
        lazy="dynamic"
    )
    chat_histories = relationship(
        "ChatHistory",
        back_populates="user",
        cascade="all, delete-orphan",
        lazy="dynamic"
    )
    wrong_questions = relationship(
        "WrongQuestion",
        back_populates="user",
        cascade="all, delete-orphan",
        lazy="dynamic"
    )

    def __repr__(self):
        return f"<User(id={self.id}, username='{self.username}', role='{self.role}')>"

    def to_dict(self):
        """转换为字典格式"""
        return {
            "id": self.id,
            "username": self.username,
            "email": self.email,
            "full_name": self.full_name,
            "role": self.role.value,
            "is_active": bool(self.is_active),
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }
