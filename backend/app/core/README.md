# 核心基础设施模块（Core）

本文件夹包含系统的基础设施和核心功能，是整个应用的"地基"。

## 📋 目录结构

```
core/
├── __init__.py       # 核心模块初始化
├── config.py         # 应用配置管理
├── database.py       # 数据库连接管理
└── security.py       # 安全功能（JWT、密码加密）
```

## 🎯 核心作用

**本文件夹是整个系统的基础设施层，提供最基础、最核心的功能。**

### 架构位置

```
┌─────────────────────────────────────┐
│         所有业务模块                 │
│   (api, services, models, etc.)     │
└──────────────┬──────────────────────┘
               ↓ 依赖
┌─────────────────────────────────────┐
│      app/core/ (基础设施层)          │
│  ├── config.py    (配置管理)         │
│  ├── database.py  (数据库连接)       │
│  └── security.py  (安全功能)         │
└─────────────────────────────────────┘
```

### 设计原则

- ✅ **最底层**：不依赖任何业务模块
- ✅ **被广泛依赖**：所有模块都依赖 core
- ✅ **单一职责**：每个文件负责一个核心功能
- ✅ **配置集中**：所有配置统一管理

---

## 📄 文件详细说明

### 1. config.py - 应用配置管理

**作用：** 集中管理所有应用配置，是系统的"配置中心"

#### 核心类：Settings

使用 Pydantic 的 `BaseSettings` 从环境变量加载配置。

#### 配置项分类

**1.1 应用配置**
```python
APP_NAME: str = "College English Assistant"  # 应用名称
APP_ENV: str = "development"                  # 运行环境（development/production）
DEBUG: bool = True                            # 调试模式
```

**1.2 服务器配置**
```python
HOST: str = "0.0.0.0"    # 服务器监听地址
PORT: int = 8000         # 服务器监听端口
```

**1.3 数据库配置**
```python
DATABASE_URL: str           # 数据库连接字符串
                           # 格式：mysql+pymysql://user:pass@host:port/db
DB_POOL_SIZE: int = 20      # 连接池大小
DB_MAX_OVERFLOW: int = 10   # 最大溢出连接数
```

**1.4 JWT 配置**
```python
SECRET_KEY: str                      # JWT 密钥（用于签名）
ALGORITHM: str = "HS256"             # 加密算法
ACCESS_TOKEN_EXPIRE_MINUTES: int = 1440  # 访问令牌过期时间（1天）
```

**1.5 LLM API 配置**
```python
LLM_PROVIDER: str            # LLM 提供商（deepseek/openai）
DEEPSEEK_API_KEY: str        # DeepSeek API 密钥
OPENAI_API_KEY: str          # OpenAI API 密钥
LLM_BASE_URL: str            # LLM API 基础地址
LLM_MODEL: str               # 使用的模型名称
LLM_TIMEOUT: int = 30        # API 请求超时时间（秒）
```

**1.6 Embedding API 配置**
```python
EMBEDDING_PROVIDER: str      # Embedding 提供商
EMBEDDING_API_KEY: str       # Embedding API 密钥
EMBEDDING_BASE_URL: str      # API 基础地址
EMBEDDING_MODEL: str         # 使用的模型名称
EMBEDDING_DIMENSION: int     # 向量维度
```

**1.7 ChromaDB 配置**
```python
CHROMA_PERSIST_DIR: str = "./data/chroma"        # 向量数据库持久化目录
CHROMA_COLLECTION_NAME: str = "course_embeddings"  # 集合名称
```

**1.8 文件上传配置**
```python
UPLOAD_DIR: str = "./uploads"        # 文件上传目录
MAX_FILE_SIZE: int = 52428800        # 最大文件大小（50MB）
```

**1.9 日志配置**
```python
LOG_LEVEL: str = "INFO"    # 日志级别（DEBUG/INFO/WARNING/ERROR）
LOG_DIR: str = "./logs"    # 日志文件目录
```

**1.10 CORS 配置**
```python
CORS_ORIGINS: List[str] = [
    "http://localhost:3000",   # React 默认端口
    "http://localhost:5173",   # Vite 默认端口
    "http://localhost:8080"    # Vue CLI 默认端口
]
```

#### 特殊功能

**自动创建目录：**
```python
def ensure_directories():
    """确保必要的目录存在"""
    dirs = [
        settings.UPLOAD_DIR,        # 上传目录
        settings.LOG_DIR,           # 日志目录
        settings.CHROMA_PERSIST_DIR # ChromaDB 目录
    ]
    for dir_path in dirs:
        Path(dir_path).mkdir(parents=True, exist_ok=True)
```

**配置加载：**
- 从 `.env` 文件加载环境变量
- 支持环境变量覆盖默认值
- 自动验证配置项类型

#### 使用示例

```python
from app.core.config import settings

# 使用配置
db_url = settings.DATABASE_URL
api_key = settings.DEEPSEEK_API_KEY
debug_mode = settings.DEBUG
```

---

### 2. database.py - 数据库连接管理

**作用：** 管理 SQLAlchemy 数据库连接和会话

#### 核心组件

**2.1 数据库引擎（Engine）**
```python
engine = create_engine(
    settings.DATABASE_URL,
    pool_size=20,           # 连接池大小
    max_overflow=10,        # 最大溢出连接数
    pool_pre_ping=True,     # 连接预检测（确保连接有效）
    pool_recycle=3600,      # 1小时回收连接（避免 MySQL 超时）
    echo=settings.DEBUG,    # 开发环境打印 SQL 语句
)
```

**连接池说明：**
- `pool_size=20`：保持 20 个活跃连接
- `max_overflow=10`：最多额外创建 10 个连接
- `pool_pre_ping=True`：每次使用前检测连接是否有效
- `pool_recycle=3600`：每小时回收连接，避免 MySQL 8 小时断开

**2.2 会话工厂（SessionLocal）**
```python
SessionLocal = sessionmaker(
    autocommit=False,  # 不自动提交
    autoflush=False,   # 不自动刷新
    bind=engine        # 绑定到引擎
)
```

**2.3 模型基类（Base）**
```python
Base = declarative_base()

# 所有模型都继承此类
class User(Base):
    __tablename__ = "users"
    ...
```

#### 核心函数

**`get_db()` - 数据库会话依赖注入**

```python
def get_db() -> Generator[Session, None, None]:
    """
    获取数据库会话的依赖注入函数
    
    用于 FastAPI 的 Depends 依赖注入
    
    Yields:
        Session: 数据库会话对象
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# 使用示例
from fastapi import Depends
from sqlalchemy.orm import Session

@router.get("/users")
def get_users(db: Session = Depends(get_db)):
    return db.query(User).all()
```

**`init_db()` - 初始化数据库**

```python
def init_db() -> None:
    """
    初始化数据库
    
    创建所有表结构（仅用于开发环境快速测试）
    生产环境应使用 Alembic 迁移
    """
    Base.metadata.create_all(bind=engine)
```

**`check_db_connection()` - 检查数据库连接**

```python
def check_db_connection() -> bool:
    """
    检查数据库连接是否正常
    
    Returns:
        bool: 连接成功返回 True，失败返回 False
    """
    try:
        with engine.connect() as conn:
            conn.execute(text("SELECT 1"))
        return True
    except Exception as e:
        logger.error(f"Database connection failed: {e}")
        return False
```

**`migrate_content_field()` - 自动迁移**

```python
def migrate_content_field() -> None:
    """
    自动迁移：将 course_documents.content 字段从 TEXT 改为 LONGTEXT
    
    在应用启动时自动执行，支持大文件上传
    """
    # 检查当前字段类型
    # 如果不是 LONGTEXT，执行 ALTER TABLE
```

#### 数据库连接流程

```
1. 应用启动
    ↓
2. 创建数据库引擎（engine）
    ↓
3. 创建会话工厂（SessionLocal）
    ↓
4. API 请求到达
    ↓
5. get_db() 创建数据库会话
    ↓
6. 执行数据库操作
    ↓
7. 请求结束，关闭会话
```

---

### 3. security.py - 安全功能

**作用：** 提供 JWT 令牌和密码加密功能

#### 核心功能

**3.1 密码加密**

使用 `bcrypt` 算法进行密码哈希。

**加密密码：**
```python
def get_password_hash(password: str) -> str:
    """
    生成密码哈希
    
    Args:
        password: 明文密码
        
    Returns:
        str: 哈希后的密码
    """
    return pwd_context.hash(password)

# 使用示例
hashed = get_password_hash("mypassword")
# 结果：$2b$12$N9qo8uLOickgx2ZMRZoMy.Mrq7...
```

**验证密码：**
```python
def verify_password(plain_password: str, hashed_password: str) -> bool:
    """
    验证密码
    
    Args:
        plain_password: 明文密码
        hashed_password: 哈希密码
        
    Returns:
        bool: 密码匹配返回 True，否则返回 False
    """
    return pwd_context.verify(plain_password, hashed_password)

# 使用示例
is_valid = verify_password("mypassword", hashed)  # True/False
```

**3.2 JWT 令牌**

使用 `python-jose` 库实现 JWT 令牌。

**创建访问令牌：**
```python
def create_access_token(data: Dict[str, Any], expires_delta: Optional[timedelta] = None) -> str:
    """
    创建 JWT 访问令牌
    
    Args:
        data: 要编码到令牌中的数据（通常是 {"sub": username}）
        expires_delta: 令牌过期时间，默认使用配置中的值
        
    Returns:
        str: JWT 令牌字符串
    """
    to_encode = data.copy()
    
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=1440)  # 1天
    
    to_encode.update({"exp": expire})
    
    encoded_jwt = jwt.encode(
        to_encode,
        settings.SECRET_KEY,
        algorithm=settings.ALGORITHM
    )
    
    return encoded_jwt

# 使用示例
token = create_access_token({"sub": "john_doe"})
# 结果：eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...
```

**解码访问令牌：**
```python
def decode_access_token(token: str) -> Optional[Dict[str, Any]]:
    """
    解码 JWT 访问令牌
    
    Args:
        token: JWT 令牌字符串
        
    Returns:
        Optional[Dict[str, Any]]: 解码后的数据，解码失败返回 None
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

# 使用示例
payload = decode_access_token(token)
if payload:
    username = payload.get("sub")
```

**创建刷新令牌：**
```python
def create_refresh_token(data: Dict[str, Any]) -> str:
    """
    创建刷新令牌（有效期更长）
    
    Args:
        data: 要编码到令牌中的数据
        
    Returns:
        str: JWT 刷新令牌字符串
    """
    to_encode = data.copy()
    # 刷新令牌有效期为 7 天
    expire = datetime.utcnow() + timedelta(days=7)
    to_encode.update({"exp": expire, "type": "refresh"})
    
    encoded_jwt = jwt.encode(
        to_encode,
        settings.SECRET_KEY,
        algorithm=settings.ALGORITHM
    )
    
    return encoded_jwt
```

**验证令牌：**
```python
def verify_token(token: str, token_type: str = "access") -> Optional[str]:
    """
    验证令牌并返回用户名
    
    Args:
        token: JWT 令牌
        token_type: 令牌类型 (access/refresh)
        
    Returns:
        Optional[str]: 用户名，验证失败返回 None
    """
    payload = decode_access_token(token)
    if not payload:
        return None
    
    # 检查令牌类型
    if token_type == "refresh" and payload.get("type") != "refresh":
        return None
    
    username = payload.get("sub")
    return username
```

#### 认证流程

```
用户登录流程：
1. 用户提交用户名和密码
    ↓
2. 查询数据库获取用户
    ↓
3. verify_password() 验证密码
    ↓
4. create_access_token() 创建访问令牌
    ↓
5. create_refresh_token() 创建刷新令牌
    ↓
6. 返回令牌给客户端

API 请求认证流程：
1. 客户端携带令牌请求（Authorization: Bearer <token>）
    ↓
2. decode_access_token() 解码令牌
    ↓
3. 验证令牌有效性和过期时间
    ↓
4. 提取用户信息（username）
    ↓
5. 查询数据库获取用户
    ↓
6. 允许访问受保护资源
```

---

## 🔧 使用指南

### 导入配置

```python
from app.core.config import settings

# 使用配置
print(settings.APP_NAME)           # College English Assistant
print(settings.DATABASE_URL)       # mysql+pymysql://...
print(settings.DEBUG)              # True
```

### 使用数据库

```python
from app.core.database import get_db, Base, engine
from sqlalchemy.orm import Session
from fastapi import Depends

# 在 API 中使用
@router.get("/items")
def get_items(db: Session = Depends(get_db)):
    items = db.query(Item).all()
    return items

# 定义模型
class Item(Base):
    __tablename__ = "items"
    id = Column(Integer, primary_key=True)
    name = Column(String(100))
```

### 使用安全功能

```python
from app.core.security import (
    get_password_hash,
    verify_password,
    create_access_token,
    decode_access_token
)

# 注册用户时加密密码
hashed_password = get_password_hash("user_password")

# 登录时验证密码
if verify_password("input_password", user.hashed_password):
    # 密码正确，创建令牌
    token = create_access_token({"sub": user.username})
    return {"access_token": token}

# 验证令牌
payload = decode_access_token(token)
if payload:
    username = payload.get("sub")
```

---

## 📊 依赖关系

```
所有业务模块
    ↓ 依赖
app/core/
    ├── config.py      ← 被所有模块依赖
    ├── database.py    ← 被 models、services、api 依赖
    └── security.py    ← 被 auth_service 依赖
```

**依赖统计：**
- `config.py` - 被所有模块依赖（配置中心）
- `database.py` - 被 models、services、api、repositories 依赖
- `security.py` - 主要被 `auth_service.py` 依赖

---

## ⚙️ 配置管理

### 环境变量

配置从 `.env` 文件加载，示例：

```env
# 应用配置
APP_ENV=development
DEBUG=True

# 数据库配置
DATABASE_URL=mysql+pymysql://root:password@localhost:3306/college_english

# JWT 配置
SECRET_KEY=your-secret-key-here

# LLM API 配置
LLM_PROVIDER=deepseek
DEEPSEEK_API_KEY=your-api-key
LLM_BASE_URL=https://api.deepseek.com/v1
LLM_MODEL=deepseek-chat

# Embedding API 配置
EMBEDDING_PROVIDER=openai
EMBEDDING_API_KEY=your-api-key
EMBEDDING_BASE_URL=https://api.openai.com/v1
EMBEDDING_MODEL=text-embedding-3-small
EMBEDDING_DIMENSION=1536
```

### 配置优先级

1. 环境变量（最高优先级）
2. `.env` 文件
3. 代码中的默认值（最低优先级）

---

## 🔒 安全注意事项

### SECRET_KEY

- ⚠️ **必须保密**：不要提交到版本控制
- ⚠️ **生产环境**：使用强随机字符串
- ⚠️ **定期更换**：建议每 3-6 个月更换

生成方法：
```python
import secrets
secret_key = secrets.token_urlsafe(32)
```

### API 密钥

- ⚠️ **不要硬编码**：使用环境变量
- ⚠️ **限制权限**：只授予必要的权限
- ⚠️ **监控使用**：定期检查 API 使用情况

---

## 📝 最佳实践

### 1. 配置管理

- ✅ 使用环境变量管理敏感信息
- ✅ 不同环境使用不同的 `.env` 文件
- ✅ 提供 `.env.example` 作为模板

### 2. 数据库连接

- ✅ 使用连接池提高性能
- ✅ 定期检查连接健康状态
- ✅ 生产环境关闭 SQL 日志（DEBUG=False）

### 3. 安全功能

- ✅ 使用强密码哈希算法（bcrypt）
- ✅ JWT 令牌设置合理的过期时间
- ✅ 敏感操作需要二次验证

---

## 📚 相关文档

- [FastAPI 配置](https://fastapi.tiangolo.com/advanced/settings/)
- [SQLAlchemy 连接池](https://docs.sqlalchemy.org/en/14/core/pooling.html)
- [JWT 最佳实践](https://auth0.com/blog/jwt-authentication-best-practices/)

---

**最后更新：** 2026-03-26
**维护人员：** 系统架构师
