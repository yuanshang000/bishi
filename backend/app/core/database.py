"""
数据库连接模块

提供SQLAlchemy数据库引擎和会话管理
"""

from sqlalchemy import create_engine, text
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, Session
from typing import Generator
import logging

from app.core.config import settings

logger = logging.getLogger(__name__)

# 创建数据库引擎
engine = create_engine(
    settings.DATABASE_URL,
    pool_size=settings.DB_POOL_SIZE,
    max_overflow=settings.DB_MAX_OVERFLOW,
    pool_pre_ping=True,  # 连接池预检测，确保连接有效
    pool_recycle=3600,   # 1小时回收连接，避免MySQL超时
    echo=settings.DEBUG,  # 开发环境打印SQL语句
)

# 创建会话工厂
SessionLocal = sessionmaker(
    autocommit=False,
    autoflush=False,
    bind=engine
)

# 创建基类
Base = declarative_base()


def get_db() -> Generator[Session, None, None]:
    """
    获取数据库会话的依赖注入函数

    用于FastAPI的Depends依赖注入

    Yields:
        Session: 数据库会话对象

    Example:
        @app.get("/users")
        def get_users(db: Session = Depends(get_db)):
            return db.query(User).all()
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def init_db() -> None:
    """
    初始化数据库

    创建所有表结构（仅用于开发环境快速测试）
    生产环境应使用Alembic迁移
    """
    logger.info("Initializing database tables...")
    Base.metadata.create_all(bind=engine)
    logger.info("Database tables created successfully")


def check_db_connection() -> bool:
    """
    检查数据库连接是否正常

    Returns:
        bool: 连接成功返回True，失败返回False
    """
    try:
        with engine.connect() as conn:
            conn.execute(text("SELECT 1"))
        logger.info("Database connection successful")
        return True
    except Exception as e:
        logger.error(f"Database connection failed: {e}")
        return False


def migrate_content_field() -> None:
    """
    自动迁移：将 course_documents.content 字段从 TEXT 改为 LONGTEXT

    在应用启动时自动执行，支持大文件上传
    """
    try:
        with engine.connect() as conn:
            # 检查当前字段类型
            result = conn.execute(text("""
                SELECT COLUMN_TYPE
                FROM INFORMATION_SCHEMA.COLUMNS
                WHERE TABLE_SCHEMA = DATABASE()
                AND TABLE_NAME = 'course_documents'
                AND COLUMN_NAME = 'content'
            """))

            row = result.fetchone()
            if row:
                current_type = row[0]
                logger.info(f"Current content column type: {current_type}")

                # 如果不是 LONGTEXT，执行迁移
                if 'longtext' not in current_type.lower():
                    logger.info("Migrating content column to LONGTEXT...")
                    conn.execute(text("""
                        ALTER TABLE course_documents
                        MODIFY COLUMN content LONGTEXT NULL
                        COMMENT '文档文本内容（支持大文件）'
                    """))
                    conn.commit()
                    logger.info("✓ Content column migrated to LONGTEXT successfully")
                else:
                    logger.info("Content column is already LONGTEXT, no migration needed")
            else:
                logger.warning("course_documents table or content column not found")

    except Exception as e:
        logger.error(f"Failed to migrate content field: {e}")
        # 不抛出异常，避免影响应用启动
