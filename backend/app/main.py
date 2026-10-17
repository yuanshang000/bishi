"""
College English Assistant - 大学英语智慧助手

主应用入口
"""

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
from fastapi.staticfiles import StaticFiles
from starlette.exceptions import HTTPException as StarletteHTTPException
import logging
import time
from pathlib import Path

from app.core.config import settings
from app.core.database import check_db_connection, migrate_content_field
from app.api.v1 import api_router

# 配置日志
logging.basicConfig(
    level=getattr(logging, settings.LOG_LEVEL),
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(f"{settings.LOG_DIR}/app.log"),
        logging.StreamHandler()
    ]
)

logger = logging.getLogger(__name__)

# 创建FastAPI应用
app = FastAPI(
    title=settings.APP_NAME,
    description="大学英语智慧助手 - 基于RAG和LLM的智能学习平台",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_url="/openapi.json"
)

# 配置CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 配置静态文件服务（用于提供音频文件）
static_dir = Path("static")
static_dir.mkdir(parents=True, exist_ok=True)
app.mount("/static", StaticFiles(directory="static"), name="static")
logger.info(f"Static files mounted at /static from {static_dir.absolute()}")


# 请求日志中间件
@app.middleware("http")
async def log_requests(request: Request, call_next):
    """记录所有HTTP请求"""
    start_time = time.time()

    # 处理请求
    response = await call_next(request)

    # 计算耗时
    process_time = time.time() - start_time

    # 记录日志
    logger.info(
        f"{request.method} {request.url.path} "
        f"Status: {response.status_code} "
        f"Time: {process_time:.3f}s"
    )

    # 添加响应头
    response.headers["X-Process-Time"] = str(process_time)

    return response


# 异常处理
@app.exception_handler(StarletteHTTPException)
async def http_exception_handler(request: Request, exc: StarletteHTTPException):
    """HTTP异常处理"""
    logger.error(f"HTTP Error: {exc.status_code} - {exc.detail}")
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "error": exc.detail,
            "status_code": exc.status_code
        }
    )


@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    """请求验证异常处理"""
    logger.error(f"Validation Error: {exc.errors()}")
    return JSONResponse(
        status_code=422,
        content={
            "error": "请求参数验证失败",
            "details": exc.errors()
        }
    )


@app.exception_handler(Exception)
async def general_exception_handler(request: Request, exc: Exception):
    """通用异常处理"""
    logger.exception(f"Unhandled Exception: {exc}")
    return JSONResponse(
        status_code=500,
        content={
            "error": "服务器内部错误",
            "message": str(exc) if settings.DEBUG else "请联系管理员"
        }
    )


# 启动事件
@app.on_event("startup")
async def startup_event():
    """应用启动时执行"""
    logger.info(f"Starting {settings.APP_NAME}...")
    logger.info(f"Environment: {settings.APP_ENV}")
    logger.info(f"Debug Mode: {settings.DEBUG}")

    # 检查数据库连接
    if check_db_connection():
        logger.info("Database connection established")

        # 自动迁移 content 字段为 LONGTEXT（支持大文件）
        migrate_content_field()
    else:
        logger.error("Failed to connect to database")

    logger.info(f"{settings.APP_NAME} started successfully!")


# 关闭事件
@app.on_event("shutdown")
async def shutdown_event():
    """应用关闭时执行"""
    logger.info(f"Shutting down {settings.APP_NAME}...")


# 健康检查
@app.get("/health", tags=["系统"])
def health_check():
    """
    健康检查接口

    返回应用状态和版本信息
    """
    db_status = "healthy" if check_db_connection() else "unhealthy"

    return {
        "status": "healthy",
        "app_name": settings.APP_NAME,
        "version": "1.0.0",
        "environment": settings.APP_ENV,
        "database": db_status
    }


# 根路径
@app.get("/", tags=["系统"])
def root():
    """
    根路径

    返回欢迎信息
    """
    return {
        "message": f"Welcome to {settings.APP_NAME}!",
        "version": "1.0.0",
        "docs": "/docs",
        "api": "/api/v1"
    }


# 注册API路由
app.include_router(api_router)


# 主函数
if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        "app.main:app",
        host=settings.HOST,
        port=settings.PORT,
        reload=False,  # 暂时禁用热重载避免日志文件触发重启
        log_level=settings.LOG_LEVEL.lower()
    )
