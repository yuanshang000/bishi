# 业务服务层（Services）

本文件夹包含系统的所有业务逻辑服务，是整个应用的核心业务处理层。

## 📋 目录结构

```
services/
├── __init__.py                      # 服务导出
├── auth_service.py                  # 认证服务
├── llm_service.py                   # 大语言模型服务
├── rag_service.py                   # RAG 检索增强生成服务
├── quiz_service.py                  # 练习服务
├── ai_analysis_service.py           # AI 学情分析服务
├── wrong_question_service.py        # 错题管理服务
├── word_training_service.py         # 单词训练服务
├── comprehensive_quiz_service.py    # 综合练习服务
├── course_parser.py                 # 课程解析服务

└── llm_service_helper.py            # LLM 服务辅助函数
```

## 🎯 核心作用

**本文件夹是系统的业务逻辑层，负责实现所有核心业务功能。**

### 架构位置

```
┌─────────────────────────────────────┐
│         API 层（路由）               │
│    - 接收请求                        │
│    - 调用服务                        │
│    - 返回响应                        │
└──────────────┬──────────────────────┘
               ↓
┌─────────────────────────────────────┐
│   Services 层（业务逻辑）← 你在这里    │
│    - 实现业务规则                     │
│    - 调用数据层                       │
│    - 调用外部服务                     │
└──────────────┬──────────────────────┘
               ↓
┌─────────────────────────────────────┐
│     Models 层 + 外部服务              │
│    - 数据库操作                       │
│    - LLM API                         │
│    - ChromaDB                        │
└─────────────────────────────────────┘
```

### 设计原则

- ✅ **业务逻辑封装**：所有业务规则在服务层实现
- ✅ **服务复用**：多个 API 可以调用同一服务
- ✅ **职责单一**：每个服务负责一个业务领域
- ✅ **依赖注入**：通过参数接收数据库会话等依赖

---

## 📊 服务概览

### 服务分类

| 分类 | 服务 | 文件大小 | 主要功能 |
|------|------|---------|---------|
| **认证授权** | AuthService | 7.6KB | 用户注册、登录、令牌验证 |
| **AI 服务** | LLMService | 112KB | LLM 调用、出题、对话 |
| **AI 服务** | RAGService | 32KB | 文档向量化、语义检索 |
| **AI 服务** | AIAnalysisService | 63KB | 学情分析、薄弱点分析 |
| **练习系统** | QuizService | 61KB | 创建练习、提交答案、评分 |
| **练习系统** | ComprehensiveQuizService | 8.5KB | 综合练习生成 |
| **练习系统** | WordTrainingService | 23KB | 单词训练 |
| **错题管理** | WrongQuestionService | 24KB | 错题记录、重做、掌握状态 |
| **课程管理** | CourseParser | 16KB | 课程内容解析 |


---

## 📄 服务详细说明

### 1. AuthService - 认证服务

**文件：** `auth_service.py` (7.6KB)

**作用：** 处理用户认证和授权相关业务

**核心功能：**

#### 用户注册
```python
@staticmethod
def register(db: Session, user_data: UserCreate) -> User:
    """
    用户注册
    
    流程：
    1. 检查用户名是否已存在
    2. 检查邮箱是否已存在
    3. 加密密码
    4. 创建用户记录
    5. 返回用户对象
    """
```

#### 用户登录
```python
@staticmethod
def login(db: Session, login_data: UserLogin) -> Token:
    """
    用户登录
    
    流程：
    1. 查询用户
    2. 验证密码
    3. 创建访问令牌
    4. 创建刷新令牌
    5. 返回令牌
    """
```

#### 令牌验证
```python
@staticmethod
def get_current_user(db: Session, token: str) -> User:
    """
    验证令牌并获取用户
    
    流程：
    1. 解码 JWT 令牌
    2. 提取用户名
    3. 查询用户
    4. 返回用户对象
    """
```

---

### 2. LLMService - 大语言模型服务

**文件：** `llm_service.py` (112KB)

**作用：** 封装大语言模型（DeepSeek/OpenAI）调用，提供 AI 能力

**核心功能：**

#### 初始化
```python
def __init__(self):
    """初始化 LLM 服务"""
    # 根据配置选择 API 提供商
    api_key = settings.DEEPSEEK_API_KEY if settings.LLM_PROVIDER == "deepseek" else settings.OPENAI_API_KEY
    
    self.client = OpenAI(
        api_key=api_key,
        base_url=settings.LLM_BASE_URL,
        timeout=settings.LLM_TIMEOUT,
    )
```

#### 聊天对话
```python
def chat(
    self,
    messages: List[Dict[str, str]],
    temperature: Optional[float] = None,
    max_tokens: Optional[int] = None,
) -> str:
    """
    发送聊天请求
    
    Args:
        messages: 消息列表 [{"role": "user", "content": "..."}]
        temperature: 温度参数（控制随机性）
        max_tokens: 最大生成 token 数
        
    Returns:
        str: LLM 响应内容
    """
```

#### 生成练习题
```python
def generate_quiz(
    self,
    context: str,
    quiz_type: str,
    count: int,
    difficulty: str,
) -> List[Dict]:
    """
    生成练习题
    
    Args:
        context: 上下文内容（课程材料）
        quiz_type: 题型（reading/translation/writing）
        count: 题目数量
        difficulty: 难度等级
        
    Returns:
        List[Dict]: 题目列表
    """
```

#### 批改答案
```python
def grade_answer(
    self,
    question: Dict,
    user_answer: str,
    correct_answer: str,
) -> Dict:
    """
    批改答案
    
    Returns:
        Dict: {
            "is_correct": bool,
            "score": float,
            "feedback": str
        }
    """
```

**支持的题型：**
- 阅读理解（reading）

- 翻译练习（translation）
- 写作练习（writing）

---

### 3. RAGService - RAG 检索增强生成服务

**文件：** `rag_service.py` (32KB)

**作用：** 实现文档向量化和语义检索功能

**核心功能：**

#### 初始化 ChromaDB
```python
def __init__(self):
    """初始化 RAG 服务"""
    # 初始化 ChromaDB 客户端
    self.chroma_client = chromadb.PersistentClient(
        path=settings.CHROMA_PERSIST_DIR,
    )
    
    # 获取或创建集合
    self.collection = self.chroma_client.get_or_create_collection(
        name=settings.CHROMA_COLLECTION_NAME,
    )
    
    # 初始化 Embedding 客户端
    self.embed_client = OpenAI(
        api_key=settings.EMBEDDING_API_KEY,
        base_url=settings.EMBEDDING_BASE_URL,
    )
```

#### 文档向量化
```python
def vectorize_document(self, db: Session, document_id: int) -> bool:
    """
    向量化文档
    
    流程：
    1. 读取文档内容
    2. 文本分块（chunking）
    3. 生成向量嵌入（embedding）
    4. 存储到 ChromaDB
    5. 更新数据库记录
    """
```

#### 语义检索
```python
def search_similar(
    self,
    query: str,
    top_k: int = 5,
) -> List[Dict]:
    """
    语义检索
    
    流程：
    1. 将查询文本向量化
    2. 在 ChromaDB 中检索相似向量
    3. 返回相似的文档片段
    
    Args:
        query: 查询文本
        top_k: 返回结果数量
        
    Returns:
        List[Dict]: 相似文档列表
    """
```

**RAG 流程：**
```
用户提问
    ↓
问题向量化
    ↓
ChromaDB 检索相似文档
    ↓
构建上下文（context）
    ↓
提供给 LLM 生成回答
```

---

### 4. QuizService - 练习服务

**文件：** `quiz_service.py` (61KB)

**作用：** 处理练习创建、提交、评分等核心业务

**核心功能：**

#### 创建练习
```python
async def create_quiz(
    self,
    db: Session,
    user_id: int,
    chapter_id: int,
    quiz_type: str,
    question_count: int,
    practice_mode: str = "chapter",
) -> QuizRecord:
    """
    创建练习
    
    流程：
    1. 获取章节内容
    2. RAG 检索相关文档
    3. 调用 LLM 生成题目
    4. 创建练习记录
    5. 返回练习对象
    """
```

#### 提交答案
```python
async def submit_quiz(
    self,
    db: Session,
    quiz_id: int,
    user_answers: List[Any],
    time_spent: int,
) -> QuizRecord:
    """
    提交练习答案
    
    流程：
    1. 获取练习记录
    2. 批改答案
    3. 计算分数和正确率
    4. 更新练习记录
    5. 记录错题
    6. 更新知识点统计
    """
```

#### 练习模式
- **章节练习**（chapter）：基于特定章节内容
- **随机练习**（random）：随机选择内容
- **综合练习**（comprehensive）：基于薄弱点生成
- **小目标练习**（subsection）：针对特定小节

---

### 5. AIAnalysisService - AI 学情分析服务

**文件：** `ai_analysis_service.py` (63KB)

**作用：** 分析学生学习情况，识别薄弱点，生成学习建议

**核心功能：**

#### 学情分析
```python
async def analyze_student_performance(
    self,
    student_id: int,
    db: Session,
) -> Dict[str, Any]:
    """
    综合分析学生学习表现
    
    返回：
    - 整体表现统计
    - 学习趋势
    - 薄弱知识点
    - 题型表现分析
    - 改进建议
    """
```

#### 薄弱点分析
```python
async def get_weak_points_detail(
    self,
    db: Session,
    student_id: int,
) -> List[Dict[str, Any]]:
    """
    获取详细的薄弱知识点分析
    
    逻辑：
    1. 查询练习记录
    2. 计算小节平均分
    3. 筛选不及格的小节（< 60分）
    4. 分析具体薄弱知识点
    5. 生成针对性建议
    """
```

#### 目标完成情况
```python
async def get_goal_completion_status(
    self,
    db: Session,
    student_id: int,
) -> List[Dict[str, Any]]:
    """
    获取目标（小节）完成情况
    
    返回：
    - 章节-节-小节层级结构
    - 每个小节的完成状态
    - 平均分、练习次数
    - 是否达标
    """
```

#### 生成分析报告
```python
def generate_analysis_report(
    self,
    analysis: Dict[str, Any],
) -> str:
    """
    生成人类可读的分析报告
    
    包含：
    - 整体表现
    - 练习方式统计
    - 题型表现分析
    - 薄弱环节分析
    - 改进建议
    """
```

---

### 6. WrongQuestionService - 错题管理服务

**文件：** `wrong_question_service.py` (24KB)

**作用：** 管理错题记录、重做、掌握状态

**核心功能：**

#### 记录错题
```python
def record_wrong_question(
    self,
    db: Session,
    user_id: int,
    quiz_record_id: int,
    question_data: Dict,
) -> WrongQuestion:
    """
    记录错题
    
    流程：
    1. 提取错题信息
    2. 创建错题记录
    3. 关联知识点
    4. 保存到数据库
    """
```

#### 重做错题
```python
async def retry_wrong_question(
    self,
    db: Session,
    wrong_question_id: int,
    user_answer: Any,
) -> Dict:
    """
    重做错题
    
    流程：
    1. 获取错题记录
    2. 批改答案
    3. 更新重做次数
    4. 如果正确，标记为已掌握
    5. 返回结果
    """
```

---

### 7. WordTrainingService - 单词训练服务

**文件：** `word_training_service.py` (23KB)

**作用：** 提供单词专项训练功能

**核心功能：**
- 生成单词默写题
- 生成单词选择题
- 单词掌握度统计
- 单词复习推荐

---

## 🔧 使用指南

### 在 API 中调用服务

```python
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from app.services.quiz_service import quiz_service
from app.api.dependencies import get_db, get_current_user

router = APIRouter()

@router.post("/quiz/create")
async def create_quiz(
    chapter_id: int,
    quiz_type: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    # 调用服务层
    quiz = await quiz_service.create_quiz(
        db=db,
        user_id=current_user.id,
        chapter_id=chapter_id,
        quiz_type=quiz_type,
        question_count=5
    )
    return quiz
```

### 服务间调用

```python
# 在一个服务中调用另一个服务
from app.services.llm_service import llm_service
from app.services.rag_service import rag_service

class QuizService:
    async def create_quiz(self, ...):
        # 调用 RAG 服务检索相关内容
        docs = rag_service.search_similar(context, top_k=5)
        
        # 调用 LLM 服务生成题目
        questions = llm_service.generate_quiz(
            context=docs,
            quiz_type=quiz_type,
            count=5
        )
        
        return questions
```

---

## 📊 服务依赖关系

```
API 层
    ↓
Services 层
    ├── AuthService → Models, Security
    ├── LLMService → OpenAI API, Tools
    ├── RAGService → ChromaDB, Embedding API
    ├── QuizService → LLMService, RAGService, Models
    ├── AIAnalysisService → data_access, Models
    ├── WrongQuestionService → Models
    └── TTSService → TTS API
```

---

## 📝 设计模式

### 1. 单例模式

大多数服务使用全局单例实例：

```python
# 创建全局实例
llm_service = LLMService()
rag_service = RAGService()
quiz_service = QuizService()

# 直接使用
result = await quiz_service.create_quiz(...)
```

### 2. 静态方法模式

部分服务使用静态方法：

```python
class AuthService:
    @staticmethod
    def register(db: Session, user_data: UserCreate) -> User:
        ...

# 调用
user = AuthService.register(db, user_data)
```

### 3. 依赖注入

通过参数接收依赖：

```python
async def create_quiz(
    self,
    db: Session,  # 注入数据库会话
    user_id: int,
    ...
):
    ...
```

---

## 📊 服务统计

| 服务 | 文件大小 | 主要方法数 | 依赖服务 |
|------|---------|-----------|---------|
| AuthService | 7.6KB | 5 | - |
| LLMService | 112KB | 20+ | - |
| RAGService | 32KB | 15+ | - |
| QuizService | 61KB | 10+ | LLM, RAG |
| AIAnalysisService | 63KB | 8 | data_access |
| WrongQuestionService | 24KB | 6 | - |
| WordTrainingService | 23KB | 8 | LLM |
| ComprehensiveQuizService | 8.5KB | 3 | LLM, RAG |
| CourseParser | 16KB | 5 | - |
| TTSService | 6KB | 2 | - |

**总计：** 10 个服务文件，约 344KB 代码

---

## 🎯 最佳实践

### 1. 服务职责单一

每个服务只负责一个业务领域：
- ✅ AuthService 只负责认证
- ✅ QuizService 只负责练习
- ❌ 不要在一个服务中混合多个业务

### 2. 服务复用

多个 API 可以调用同一服务：
```python
# API 1
@router.post("/quiz/create")
async def create_quiz(...):
    return await quiz_service.create_quiz(...)

# API 2
@router.post("/quiz/random")
async def random_quiz(...):
    return await quiz_service.create_quiz(...)  # 复用同一服务
```

### 3. 错误处理

服务层应该抛出明确的异常：
```python
if not user:
    raise HTTPException(
        status_code=status.HTTP_404_NOT_FOUND,
        detail="用户不存在"
    )
```

### 4. 日志记录

关键操作应该记录日志：
```python
logger.info(f"Creating quiz for user {user_id}")
logger.error(f"Failed to generate questions: {e}")
```

---

## 📚 相关文档

- [FastAPI 依赖注入](https://fastapi.tiangolo.com/tutorial/dependencies/)
- [SQLAlchemy 会话管理](https://docs.sqlalchemy.org/en/14/orm/session.html)
- [OpenAI API 文档](https://platform.openai.com/docs/)

---

**最后更新：** 2026-03-26
**维护人员：** 业务架构师
