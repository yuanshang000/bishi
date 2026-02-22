"""
MCP Server Configuration

配置数据库连接和服务器参数
"""

from pydantic_settings import BaseSettings
from pydantic import ConfigDict
from typing import Optional


class MCPSettings(BaseSettings):
    """MCP 服务配置"""

    # 数据库配置
    DATABASE_URL: str = "mysql+pymysql://root:123456@localhost:3306/college_english_assistant"

    # MCP Server 配置
    SERVER_NAME: str = "student-analytics"
    SERVER_VERSION: str = "1.0.0"

    # 日志配置
    LOG_LEVEL: str = "INFO"

    model_config = ConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore"  # 忽略额外的环境变量字段
    )


# 创建全局配置实例
settings = MCPSettings()
