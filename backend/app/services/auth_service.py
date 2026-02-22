"""
认证服务

提供用户注册、登录、令牌验证等功能
"""

from typing import Optional
from sqlalchemy.orm import Session
from fastapi import HTTPException, status
import logging

from app.models.user import User, UserRole
from app.schemas.user import UserCreate, UserLogin, Token
from app.core.security import (
    verify_password,
    get_password_hash,
    create_access_token,
    create_refresh_token,
    verify_token,
)

logger = logging.getLogger(__name__)


class AuthService:
    """认证服务类"""

    @staticmethod
    def register(db: Session, user_data: UserCreate) -> User:
        """
        用户注册

        Args:
            db: 数据库会话
            user_data: 用户注册数据

        Returns:
            User: 创建的用户对象

        Raises:
            HTTPException: 用户名已存在时抛出
        """
        # 检查用户名是否已存在
        existing_user = db.query(User).filter(User.username == user_data.username).first()
        if existing_user:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="用户名已存在"
            )

        # 检查邮箱是否已存在
        if user_data.email:
            existing_email = db.query(User).filter(User.email == user_data.email).first()
            if existing_email:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="邮箱已被注册"
                )

        # 创建用户
        user = User(
            username=user_data.username,
            email=user_data.email,
            full_name=user_data.full_name,
            password_hash=get_password_hash(user_data.password),
            role=UserRole(user_data.role),
        )

        db.add(user)
        db.commit()
        db.refresh(user)

        logger.info(f"User registered: {user.username} (ID: {user.id})")
        return user

    @staticmethod
    def login(db: Session, login_data: UserLogin) -> Token:
        """
        用户登录

        Args:
            db: 数据库会话
            login_data: 登录数据

        Returns:
            Token: JWT令牌

        Raises:
            HTTPException: 用户名或密码错误时抛出
        """
        # 查找用户
        user = db.query(User).filter(User.username == login_data.username).first()
        if not user:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="用户名或密码错误",
                headers={"WWW-Authenticate": "Bearer"},
            )

        # 验证密码
        if not verify_password(login_data.password, user.password_hash):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="用户名或密码错误",
                headers={"WWW-Authenticate": "Bearer"},
            )

        # 检查账号状态
        if not user.is_active:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="账号已被禁用"
            )

        # 生成令牌
        token_data = {
            "sub": user.username,
            "user_id": user.id,
            "role": user.role.value,
        }

        access_token = create_access_token(token_data)
        refresh_token = create_refresh_token(token_data)

        logger.info(f"User logged in: {user.username} (ID: {user.id})")

        return Token(
            access_token=access_token,
            refresh_token=refresh_token,
            token_type="bearer"
        )

    @staticmethod
    def get_current_user(db: Session, token: str) -> User:
        """
        获取当前用户

        Args:
            db: 数据库会话
            token: JWT令牌

        Returns:
            User: 当前用户对象

        Raises:
            HTTPException: 令牌无效时抛出
        """
        username = verify_token(token)
        if not username:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="无效的认证凭证",
                headers={"WWW-Authenticate": "Bearer"},
            )

        user = db.query(User).filter(User.username == username).first()
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="用户不存在"
            )

        if not user.is_active:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="账号已被禁用"
            )

        return user

    @staticmethod
    def refresh_access_token(db: Session, refresh_token: str) -> Token:
        """
        刷新访问令牌

        Args:
            db: 数据库会话
            refresh_token: 刷新令牌

        Returns:
            Token: 新的JWT令牌

        Raises:
            HTTPException: 刷新令牌无效时抛出
        """
        username = verify_token(refresh_token, token_type="refresh")
        if not username:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="无效的刷新令牌",
                headers={"WWW-Authenticate": "Bearer"},
            )

        user = db.query(User).filter(User.username == username).first()
        if not user or not user.is_active:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="用户不存在或已被禁用"
            )

        # 生成新令牌
        token_data = {
            "sub": user.username,
            "user_id": user.id,
            "role": user.role.value,
        }

        access_token = create_access_token(token_data)

        return Token(
            access_token=access_token,
            token_type="bearer"
        )

    @staticmethod
    def get_user_by_id(db: Session, user_id: int) -> Optional[User]:
        """
        根据ID获取用户

        Args:
            db: 数据库会话
            user_id: 用户ID

        Returns:
            Optional[User]: 用户对象，不存在返回None
        """
        return db.query(User).filter(User.id == user_id).first()

    @staticmethod
    def update_user(db: Session, user_id: int, **kwargs) -> User:
        """
        更新用户信息

        Args:
            db: 数据库会话
            user_id: 用户ID
            **kwargs: 要更新的字段

        Returns:
            User: 更新后的用户对象

        Raises:
            HTTPException: 用户不存在时抛出
        """
        user = db.query(User).filter(User.id == user_id).first()
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="用户不存在"
            )

        # 如果更新密码，需要加密
        if 'password' in kwargs:
            kwargs['password_hash'] = get_password_hash(kwargs.pop('password'))

        # 更新字段
        for key, value in kwargs.items():
            if hasattr(user, key) and value is not None:
                setattr(user, key, value)

        db.commit()
        db.refresh(user)

        logger.info(f"User updated: {user.username} (ID: {user.id})")
        return user
