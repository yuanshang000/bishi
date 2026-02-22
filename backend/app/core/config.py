"""
核心配置模块

从环境变量和配置文件加载应用配置
"""

from typing import List
from pydantic_settings import BaseSettings
from pydantic import validator
import os
from pathlib import Path


class Settings(BaseSettings):
    """应用配置"""

    # 应用配置
    APP_NAME: str = "College English Assistant"
    APP_ENV: str = "development"
    DEBUG: bool = True

    # 服务器配置
    HOST: str = "0.0.0.0"
    PORT: int = 8000

    # 数据库配置
    DATABASE_URL: str
    DB_POOL_SIZE: int = 20
    DB_MAX_OVERFLOW: int = 10

    # JWT配置
    SECRET_KEY: str
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 1440

    # LLM API配置
    LLM_PROVIDER: str
    DEEPSEEK_API_KEY: str = ""
    OPENAI_API_KEY: str = ""
    LLM_BASE_URL: str
    LLM_MODEL: str
    LLM_TIMEOUT: int = 30

    # Embedding API配置
    EMBEDDING_PROVIDER: str
    EMBEDDING_API_KEY: str
    EMBEDDING_BASE_URL: str
    EMBEDDING_MODEL: str
    EMBEDDING_DIMENSION: int

    # ChromaDB配置
    CHROMA_PERSIST_DIR: str = "./data/chroma"
    CHROMA_COLLECTION_NAME: str = "course_embeddings"

    # 文件上传配置
    UPLOAD_DIR: str = "./uploads"
    MAX_FILE_SIZE: int = 52428800  # 50MB

    # 日志配置
    LOG_LEVEL: str = "INFO"
    LOG_DIR: str = "./logs"

    # CORS配置
    CORS_ORIGINS: List[str] = [
        "http://localhost:3000",
        "http://localhost:5173",
        "http://localhost:8080"
    ]

    @validator("CORS_ORIGINS", pre=True)
    def parse_cors_origins(cls, v):
        """解析CORS配置"""
        if isinstance(v, str):
            # 如果是字符串，尝试解析为列表
            import json
            try:
                return json.loads(v)
            except:
                return [origin.strip() for origin in v.split(",")]
        return v

    class Config:
        env_file = ".env"
        case_sensitive = True


# 创建全局配置实例
settings = Settings()


# 确保必要的目录存在
def ensure_directories():
    """确保必要的目录存在"""
    dirs = [
        settings.UPLOAD_DIR,
        settings.LOG_DIR,
        settings.CHROMA_PERSIST_DIR,
    ]

    for dir_path in dirs:
        Path(dir_path).mkdir(parents=True, exist_ok=True)


# 应用启动时调用
ensure_directories()
