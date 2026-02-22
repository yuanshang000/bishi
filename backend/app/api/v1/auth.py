"""
认证相关API路由
"""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.schemas.user import UserCreate, UserLogin, UserResponse, Token
from app.services.auth_service import AuthService
from app.api.dependencies import get_db, get_current_active_user
from app.models.user import User

router = APIRouter(prefix="/auth", tags=["认证"])


@router.post("/register", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
def register(
    user_data: UserCreate,
    db: Session = Depends(get_db)
):
    """
    用户注册

    - **username**: 用户名（3-50字符）
    - **password**: 密码（6-50字符）
    - **email**: 邮箱（可选）
    - **full_name**: 真实姓名（可选）
    - **role**: 角色，可选值: teacher, student（默认: student）
    """
    user = AuthService.register(db, user_data)
    return user


@router.post("/login", response_model=Token)
def login(
    login_data: UserLogin,
    db: Session = Depends(get_db)
):
    """
    用户登录

    - **username**: 用户名
    - **password**: 密码

    返回JWT访问令牌和刷新令牌
    """
    token = AuthService.login(db, login_data)
    return token


@router.post("/refresh", response_model=Token)
def refresh_token(
    refresh_token: str,
    db: Session = Depends(get_db)
):
    """
    刷新访问令牌

    - **refresh_token**: 刷新令牌

    返回新的访问令牌
    """
    token = AuthService.refresh_access_token(db, refresh_token)
    return token


@router.get("/me", response_model=UserResponse)
def get_current_user_info(
    current_user: User = Depends(get_current_active_user)
):
    """
    获取当前用户信息

    需要认证
    """
    return current_user


@router.get("/users/{user_id}", response_model=UserResponse)
def get_user_by_id(
    user_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """
    根据ID获取用户信息

    需要认证
    """
    user = AuthService.get_user_by_id(db, user_id)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="用户不存在"
        )
    return user
