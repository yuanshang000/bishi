"""
数据访问层配置

配置数据库连接和日志参数
"""

from pydantic_settings import BaseSettings
from pydantic import ConfigDict
from typing import Optional


class DataAccessSettings(BaseSettings):
    """
    数据访问层配置
    
    【说明】
    本配置用于数据访问层（Data Access Layer）的数据库连接和日志设置。
    """

    # 数据库配置
    DATABASE_URL: str = "mysql+pymysql://root:your_password@localhost:3306/college_english_assistant"

    # 日志配置
    LOG_LEVEL: str = "INFO"

    model_config = ConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore"  # 忽略额外的环境变量字段
    )


# 创建全局配置实例
settings = DataAccessSettings()
