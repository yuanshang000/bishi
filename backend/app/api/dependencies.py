"""
依赖注入模块

提供FastAPI依赖函数
"""

from typing import Generator
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.orm import Session

from app.core.database import SessionLocal
from app.models.user import User
from app.services.auth_service import AuthService

# HTTP Bearer认证方案
security = HTTPBearer()


def get_db() -> Generator[Session, None, None]:
    """
    获取数据库会话

    Yields:
        Session: 数据库会话
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: Session = Depends(get_db)
) -> User:
    """
    获取当前认证用户

    Args:
        credentials: HTTP Bearer凭证
        db: 数据库会话

    Returns:
        User: 当前用户

    Raises:
        HTTPException: 认证失败时抛出
    """
    token = credentials.credentials
    return AuthService.get_current_user(db, token)


def get_current_active_user(
    current_user: User = Depends(get_current_user)
) -> User:
    """
    获取当前活跃用户

    Args:
        current_user: 当前用户

    Returns:
        User: 当前活跃用户

    Raises:
        HTTPException: 用户未激活时抛出
    """
    if not current_user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="账号已被禁用"
        )
    return current_user


def require_teacher(
    current_user: User = Depends(get_current_active_user)
) -> User:
    """
    要求教师权限

    Args:
        current_user: 当前用户

    Returns:
        User: 教师用户

    Raises:
        HTTPException: 非教师时抛出
    """
    if current_user.role.value != "teacher":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="需要教师权限"
        )
    return current_user
