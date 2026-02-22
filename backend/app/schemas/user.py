"""
用户相关的Pydantic模式
"""

from typing import Optional
from pydantic import BaseModel, EmailStr, Field
from datetime import datetime


class UserBase(BaseModel):
    """用户基础模式"""
    username: str = Field(..., min_length=3, max_length=50, description="用户名")
    email: Optional[EmailStr] = Field(None, description="电子邮箱")
    full_name: Optional[str] = Field(None, max_length=100, description="真实姓名")


class UserCreate(UserBase):
    """用户创建模式"""
    password: str = Field(..., min_length=6, max_length=50, description="密码")
    role: str = Field(default="student", description="用户角色 (teacher/student)")


class UserUpdate(BaseModel):
    """用户更新模式"""
    email: Optional[EmailStr] = None
    full_name: Optional[str] = None
    password: Optional[str] = Field(None, min_length=6, max_length=50)
    is_active: Optional[bool] = None


class UserResponse(UserBase):
    """用户响应模式"""
    id: int
    role: str
    is_active: bool
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class UserLogin(BaseModel):
    """用户登录模式"""
    username: str = Field(..., description="用户名")
    password: str = Field(..., description="密码")


class Token(BaseModel):
    """令牌响应模式"""
    access_token: str
    refresh_token: Optional[str] = None
    token_type: str = "bearer"


class TokenData(BaseModel):
    """令牌数据模式"""
    username: Optional[str] = None
    user_id: Optional[int] = None
    role: Optional[str] = None
