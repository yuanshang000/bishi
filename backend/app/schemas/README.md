# 数据验证模式层（Schemas）

本文件夹包含系统的所有 Pydantic 数据验证模式，用于 API 请求验证和响应序列化。

## 📋 目录结构

```
schemas/
├── __init__.py          # 模式导出
├── user.py              # 用户相关模式
├── chapter.py           # 章节相关模式
├── section.py           # 节相关模式
├── subsection.py        # 小节相关模式
├── document.py          # 文档相关模式
├── quiz.py              # 练习相关模式
├── chat.py              # 聊天相关模式
└── wrong_question.py    # 错题相关模式
```

## 🎯 核心作用

**本文件夹是系统的数据验证层，负责 API 请求验证、响应序列化和数据转换。**

### 架构位置

```
┌─────────────────────────────────────┐
│         前端请求（JSON）              │
└──────────────┬──────────────────────┘
               ↓
┌─────────────────────────────────────┐
│   Schemas 层（数据验证）← 你在这里     │
│   - 请求验证                          │
│   - 类型转换                          │
│   - 响应序列化                        │
└──────────────┬──────────────────────┘
               ↓
┌─────────────────────────────────────┐
│         API 层（路由处理）             │
└──────────────┬──────────────────────┘
               ↓
┌─────────────────────────────────────┐
│       Services 层（业务逻辑）          │
└─────────────────────────────────────┘
```

### 设计原则

- ✅ **请求验证**：验证前端提交的数据格式
- ✅ **类型安全**：使用 Pydantic 进行类型检查
- ✅ **响应序列化**：将模型转换为 JSON 响应
- ✅ **文档生成**：自动生成 API 文档

---

## 📊 模式分类

### 模式类型

| 类型 | 命名规则 | 用途 | 示例 |
|------|---------|------|------|
| **Base** | `XxxBase` | 基础字段定义 | UserBase |
| **Create** | `XxxCreate` | 创建请求验证 | UserCreate |
| **Update** | `XxxUpdate` | 更新请求验证 | UserUpdate |
| **Response** | `XxxResponse` | 响应数据序列化 | UserResponse |
| **特殊** | 自定义 | 特定场景验证 | UserLogin, Token |

---

## 📄 模式详细说明

### 1. user.py - 用户相关模式

**包含模式：**

#### UserBase - 用户基础模式
```python
class UserBase(BaseModel):
    """用户基础模式"""
    username: str = Field(..., min_length=3, max_length=50, description="用户名")
    email: Optional[EmailStr] = Field(None, description="电子邮箱")
    full_name: Optional[str] = Field(None, max_length=100, description="真实姓名")
```

**用途：** 定义用户的基本字段，被其他模式继承

#### UserCreate - 用户创建模式
```python
class UserCreate(UserBase):
    """用户创建模式"""
    password: str = Field(..., min_length=6, max_length=50, description="密码")
    role: str = Field(default="student", description="用户角色 (teacher/student)")
```

**用途：** 验证用户注册请求

**验证规则：**
- username: 3-50 字符
- password: 6-50 字符
- email: 邮箱格式（可选）
- role: 默认为 student

#### UserUpdate - 用户更新模式
```python
class UserUpdate(BaseModel):
    """用户更新模式"""
    email: Optional[EmailStr] = None
    full_name: Optional[str] = None
    password: Optional[str] = Field(None, min_length=6, max_length=50)
    is_active: Optional[bool] = None
```

**用途：** 验证用户信息更新请求

**特点：** 所有字段都是可选的，支持部分更新

#### UserResponse - 用户响应模式
```python
class UserResponse(UserBase):
    """用户响应模式"""
    id: int
    role: str
    is_active: bool
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True  # 支持从 ORM 模型转换
```

**用途：** 序列化用户数据返回给前端

**特点：**
- 包含数据库生成的字段（id, created_at）
- `from_attributes=True` 支持从 SQLAlchemy 模型转换

#### UserLogin - 用户登录模式
```python
class UserLogin(BaseModel):
    """用户登录模式"""
    username: str = Field(..., description="用户名")
    password: str = Field(..., description="密码")
```

**用途：** 验证用户登录请求

#### Token - 令牌响应模式
```python
class Token(BaseModel):
    """令牌响应模式"""
    access_token: str
    refresh_token: Optional[str] = None
    token_type: str = "bearer"
```

**用途：** 返回 JWT 令牌给前端

#### TokenData - 令牌数据模式
```python
class TokenData(BaseModel):
    """令牌数据模式"""
    username: Optional[str] = None
    user_id: Optional[int] = None
    role: Optional[str] = None
```

**用途：** 解析 JWT 令牌中的数据

---

### 2. chapter.py - 章节相关模式

**包含模式：**

#### ChapterBase - 章节基础模式
```python
class ChapterBase(BaseModel):
    """章节基础模式"""
    chapter_number: int = Field(..., description="章节编号")
    title: str = Field(..., max_length=200, description="章节标题")
    description: Optional[str] = Field(None, description="章节描述")
    learning_objectives: Optional[List[str]] = Field(None, description="学习目标")
    key_points: Optional[List[str]] = Field(None, description="知识点列表")
```

#### ChapterCreate - 章节创建模式
```python
class ChapterCreate(ChapterBase):
    """章节创建模式"""
    word_count: Optional[int] = Field(0, description="词汇量")
    difficulty_level: Optional[str] = Field("intermediate", description="难度等级")
```

#### ChapterUpdate - 章节更新模式
```python
class ChapterUpdate(BaseModel):
    """章节更新模式"""
    title: Optional[str] = Field(None, max_length=200)
    description: Optional[str] = None
    learning_objectives: Optional[List[str]] = None
    key_points: Optional[List[str]] = None
    word_count: Optional[int] = None
    difficulty_level: Optional[str] = None
```

#### ChapterResponse - 章节响应模式
```python
class ChapterResponse(ChapterBase):
    """章节响应模式"""
    id: int
    word_count: int
    difficulty_level: str
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True
```

---

### 3. quiz.py - 练习相关模式

**包含模式：**

#### QuestionBase - 题目基础模式
```python
class QuestionBase(BaseModel):
    """题目基础模式"""
    question_type: str = Field(..., description="题目类型")
    question_text: str = Field(..., description="题目内容")
    options: Optional[List[str]] = Field(None, description="选项列表（选择题）")
    correct_answer: Any = Field(..., description="正确答案")
    explanation: Optional[str] = Field(None, description="答案解析")
```

#### QuizBase - 练习基础模式
```python
class QuizBase(BaseModel):
    """练习基础模式"""
    chapter_id: Optional[int] = Field(None, description="章节ID")
    subsection_id: Optional[int] = Field(None, description="小目标ID")
    practice_mode: str = Field("chapter", description="练习方式")
    quiz_type: str = Field(..., description="练习类型")
    difficulty: str = Field("intermediate", description="难度等级")
```

#### QuizCreate - 练习创建模式
```python
class QuizCreate(QuizBase):
    """练习创建模式"""
    question_count: int = Field(5, ge=1, le=20, description="题目数量")
```

**验证规则：**
- question_count: 1-20 之间

#### QuizSubmit - 练习提交模式
```python
class QuizSubmit(BaseModel):
    """练习提交模式"""
    quiz_id: int = Field(..., description="练习记录ID")
    user_answers: List[Any] = Field(..., description="用户答案列表")
    time_spent: Optional[int] = Field(None, description="用时（秒）")
```

#### QuizResponse - 练习响应模式
```python
class QuizResponse(QuizBase):
    """练习响应模式"""
    id: int
    user_id: int
    question_count: int
    questions: Optional[List[Dict[str, Any]]]
    user_answers: Optional[List[Any]] = None
    score: float
    accuracy: float
    time_spent: int
    is_completed: bool
    started_at: Optional[datetime]
    completed_at: Optional[datetime]
```

**特殊字段：**
- `source_documents`: 出题使用的文档列表
- `source_chunks`: RAG 检索使用的分块预览
- `rag_context`: 传入 AI 的上下文文本
- `applied_rules`: 本次出题使用的规则摘要

---

### 4. document.py - 文档相关模式

**包含模式：**

#### DocumentUpload - 文档上传模式
```python
class DocumentUpload(BaseModel):
    """文档上传模式"""
    chapter_id: int = Field(..., description="章节ID")
    file_type: str = Field(..., description="文件类型")
```

#### DocumentResponse - 文档响应模式
```python
class DocumentResponse(BaseModel):
    """文档响应模式"""
    id: int
    chapter_id: int
    title: str
    file_path: str
    file_type: str
    file_size: int
    is_vectorized: bool
    vector_count: int
    created_at: datetime
```

---

### 5. chat.py - 聊天相关模式

**包含模式：**

#### ChatRequest - 聊天请求模式
```python
class ChatRequest(BaseModel):
    """聊天请求模式"""
    message: str = Field(..., description="用户消息")
    chapter_id: Optional[int] = Field(None, description="章节ID")
    session_id: Optional[str] = Field(None, description="会话ID")
    use_rag: bool = Field(True, description="是否使用RAG检索")
    mode: str = Field("chat", description="模式 (chat/quiz)")
```

#### ChatResponse - 聊天响应模式
```python
class ChatResponse(BaseModel):
    """聊天响应模式"""
    message: str
    session_id: str
    sources: Optional[List[Dict[str, Any]]] = None
    created_at: datetime
```

#### ChatMessage - 聊天消息模式
```python
class ChatMessage(BaseModel):
    """聊天消息模式"""
    role: str  # user/assistant
    content: str
    timestamp: datetime
```

---

### 6. wrong_question.py - 错题相关模式

**包含模式：**

#### WrongQuestionResponse - 错题响应模式
```python
class WrongQuestionResponse(BaseModel):
    """错题响应模式"""
    id: int
    question_type: str
    question_data: Dict[str, Any]
    user_answer: Any
    correct_answer: Any
    is_mastered: bool
    retry_count: int
    created_at: datetime
```

---

## 🔧 使用指南

### 在 API 中使用

#### 1. 请求验证

```python
from fastapi import APIRouter, Depends
from app.schemas.user import UserCreate, UserResponse

@router.post("/register", response_model=UserResponse)
def register(user_data: UserCreate):
    """
    用户注册
    
    - user_data 会自动验证：
      - username: 3-50 字符
      - password: 6-50 字符
      - email: 邮箱格式
    """
    # 如果验证失败，FastAPI 会自动返回 422 错误
    user = AuthService.register(user_data)
    return user
```

#### 2. 响应序列化

```python
from app.schemas.chapter import ChapterResponse

@router.get("/chapters/{chapter_id}", response_model=ChapterResponse)
def get_chapter(chapter_id: int, db: Session = Depends(get_db)):
    """
    获取章节详情
    
    - 返回的数据会自动按 ChapterResponse 格式序列化
    - 只返回定义的字段，忽略其他字段
    """
    chapter = db.query(Chapter).filter(Chapter.id == chapter_id).first()
    return chapter  # 自动转换为 ChapterResponse
```

#### 3. 嵌套模型

```python
from app.schemas.quiz import QuizResponse, QuestionBase

@router.get("/quiz/{quiz_id}", response_model=QuizResponse)
def get_quiz(quiz_id: int):
    quiz = get_quiz_from_db(quiz_id)
    return quiz  # questions 字段会自动验证为 List[QuestionBase]
```

---

## 📝 Pydantic 特性

### 1. 字段验证

```python
from pydantic import BaseModel, Field

class Example(BaseModel):
    # 必填字段
    name: str = Field(..., description="名称")
    
    # 可选字段
    age: Optional[int] = Field(None, description="年龄")
    
    # 带约束的字段
    score: int = Field(..., ge=0, le=100, description="分数（0-100）")
    
    # 带长度限制的字段
    username: str = Field(..., min_length=3, max_length=50)
```

**常用约束：**
- `ge` / `gt`: 大于等于 / 大于
- `le` / `lt`: 小于等于 / 小于
- `min_length` / `max_length`: 字符串长度
- `regex`: 正则表达式匹配

### 2. 类型转换

```python
class Example(BaseModel):
    # 自动类型转换
    age: int  # "25" → 25
    price: float  # "99.99" → 99.99
    is_active: bool  # "true" → True
```

### 3. 嵌套模型

```python
class Address(BaseModel):
    city: str
    street: str

class User(BaseModel):
    name: str
    address: Address  # 嵌套模型
```

### 4. 列表和字典

```python
class Example(BaseModel):
    tags: List[str]  # 字符串列表
    metadata: Dict[str, Any]  # 字典
```

### 5. 自定义验证器

```python
from pydantic import field_validator

class User(BaseModel):
    username: str
    
    @field_validator('username')
    def validate_username(cls, v):
        if not v.isalnum():
            raise ValueError('用户名只能包含字母和数字')
        return v
```

---

## 🔄 模式继承关系

```
BaseModel (Pydantic)
    ↓
UserBase
    ├── UserCreate (添加 password, role)
    └── UserResponse (添加 id, created_at 等)

ChapterBase
    ├── ChapterCreate (添加 word_count 等)
    └── ChapterResponse (添加 id, created_at 等)

QuizBase
    ├── QuizCreate (添加 question_count)
    └── QuizResponse (添加所有响应字段)
```

---

## 📊 模式统计

| 文件 | 模式数量 | 主要模式 |
|------|---------|---------|
| user.py | 7 | UserCreate, UserResponse, Token |
| chapter.py | 4 | ChapterCreate, ChapterResponse |
| section.py | 4 | SectionCreate, SectionResponse |
| subsection.py | 4 | SubSectionCreate, SubSectionResponse |
| document.py | 4 | DocumentUpload, DocumentResponse |
| quiz.py | 10+ | QuizCreate, QuizSubmit, QuizResponse |
| chat.py | 5 | ChatRequest, ChatResponse |
| wrong_question.py | 3 | WrongQuestionResponse |

**总计：** 8 个文件，40+ 个模式类

---

## 🎯 设计模式

### 1. Base-Create-Update-Response 模式

这是最常用的模式组合：

```python
# 基础字段
class UserBase(BaseModel):
    username: str
    email: Optional[str]

# 创建请求（继承 Base，添加必填字段）
class UserCreate(UserBase):
    password: str

# 更新请求（所有字段可选）
class UserUpdate(BaseModel):
    email: Optional[str]
    password: Optional[str]

# 响应（继承 Base，添加系统字段）
class UserResponse(UserBase):
    id: int
    created_at: datetime
```

### 2. 请求-响应分离

```python
# 请求模式
class QuizCreate(BaseModel):
    chapter_id: int
    question_count: int

# 响应模式
class QuizResponse(BaseModel):
    id: int
    questions: List[Dict]
    score: float
```

---

## 📚 相关文档

- [Pydantic 官方文档](https://docs.pydantic.dev/)
- [FastAPI 请求体](https://fastapi.tiangolo.com/tutorial/body/)
- [FastAPI 响应模型](https://fastapi.tiangolo.com/tutorial/response-model/)

---

**最后更新：** 2026-03-26
**维护人员：** API 架构师
