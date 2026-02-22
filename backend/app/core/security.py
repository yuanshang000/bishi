"""
安全模块

提供JWT令牌生成/验证和密码加密/验证功能
"""

from datetime import datetime, timedelta
from typing import Optional, Dict, Any
from jose import JWTError, jwt
from passlib.context import CryptContext
import logging

from app.core.config import settings

logger = logging.getLogger(__name__)

# 密码加密上下文
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """
    验证密码

    Args:
        plain_password: 明文密码
        hashed_password: 哈希密码

    Returns:
        bool: 密码匹配返回True，否则返回False
    """
    return pwd_context.verify(plain_password, hashed_password)


def get_password_hash(password: str) -> str:
    """
    生成密码哈希

    Args:
        password: 明文密码

    Returns:
        str: 哈希后的密码
    """
    return pwd_context.hash(password)


def create_access_token(data: Dict[str, Any], expires_delta: Optional[timedelta] = None) -> str:
    """
    创建JWT访问令牌

    Args:
        data: 要编码到令牌中的数据
        expires_delta: 令牌过期时间，默认使用配置中的值

    Returns:
        str: JWT令牌字符串
    """
    to_encode = data.copy()

    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)

    to_encode.update({"exp": expire})

    encoded_jwt = jwt.encode(
        to_encode,
        settings.SECRET_KEY,
        algorithm=settings.ALGORITHM
    )

    return encoded_jwt


def decode_access_token(token: str) -> Optional[Dict[str, Any]]:
    """
    解码JWT访问令牌

    Args:
        token: JWT令牌字符串

    Returns:
        Optional[Dict[str, Any]]: 解码后的数据，解码失败返回None
    """
    try:
        payload = jwt.decode(
            token,
            settings.SECRET_KEY,
            algorithms=[settings.ALGORITHM]
        )
        return payload
    except JWTError as e:
        logger.error(f"JWT decode error: {e}")
        return None


def create_refresh_token(data: Dict[str, Any]) -> str:
    """
    创建刷新令牌（有效期更长）

    Args:
        data: 要编码到令牌中的数据

    Returns:
        str: JWT刷新令牌字符串
    """
    to_encode = data.copy()
    # 刷新令牌有效期为7天
    expire = datetime.utcnow() + timedelta(days=7)
    to_encode.update({"exp": expire, "type": "refresh"})

    encoded_jwt = jwt.encode(
        to_encode,
        settings.SECRET_KEY,
        algorithm=settings.ALGORITHM
    )

    return encoded_jwt


def verify_token(token: str, token_type: str = "access") -> Optional[str]:
    """
    验证令牌并返回用户名

    Args:
        token: JWT令牌
        token_type: 令牌类型 (access/refresh)

    Returns:
        Optional[str]: 用户名，验证失败返回None
    """
    payload = decode_access_token(token)
    if not payload:
        return None

    # 检查令牌类型
    if token_type == "refresh" and payload.get("type") != "refresh":
        return None

    username = payload.get("sub")
    return username
