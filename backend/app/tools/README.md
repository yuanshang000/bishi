# 工具层（Tools）

本文件夹包含 LLM 工具调用的定义和实现，用于让 AI 模型调用后端功能。

## 📋 目录结构

```
tools/
├── __init__.py              # 工具导出
├── tool_definitions.py      # 工具定义（OpenAI Function Calling 格式）
├── data_tools.py            # 数据查询工具实现
└── quiz_tools.py            # 练习生成工具实现
```

## 🎯 核心作用

**本文件夹实现了 LLM 的工具调用（Tool Calling）功能，专门用于 AI 智能问答页面。**

### 使用场景

**这些工具仅用于 AI 智能问答功能，不涉及练习中心！**

- ✅ **AI 智能问答页面**：用户与 AI 对话时，AI 可以调用这些工具
- ❌ **练习中心**：练习中心有独立的 QuizService，不使用这些工具

**调用路径：**
```
AI 智能问答页面
    ↓
chat.py API (/api/v1/chat)
    ↓
llm_service.answer_question()
    ↓
工具调用（Tools）
    ↓
返回结果给 AI
```

### 架构位置

```
┌─────────────────────────────────────┐
│   AI 智能问答页面（前端）             │
│    - 用户输入问题                     │
│    - 显示 AI 回复                     │
└──────────────┬──────────────────────┘
               ↓
┌─────────────────────────────────────┐
│   chat.py API (/api/v1/chat)        │
│    - 接收聊天请求                     │
│    - 调用 LLM Service                │
└──────────────┬──────────────────────┘
               ↓
┌─────────────────────────────────────┐
│   LLM Service (answer_question)     │
│    - 判断是否需要调用工具             │
│    - 执行工具调用                     │
└──────────────┬──────────────────────┘
               ↓
┌─────────────────────────────────────┐
│   Tools 层 ← 你在这里                │
│    - 工具定义（TOOL_DEFINITIONS）    │
│    - 工具实现（具体函数）             │
└──────────────┬──────────────────────┘
               ↓
┌─────────────────────────────────────┐
│     Services + Models                │
│    - 业务逻辑                         │
│    - 数据库查询                       │
│    - RAG 检索                         │
└─────────────────────────────────────┘
```

**注意：练习中心不经过这个流程！**

练习中心直接调用：
```
练习中心页面
    ↓
quiz.py API (/api/v1/quiz)
    ↓
QuizService
    ↓
LLMService.generate_quiz()
```

### 工作原理

1. **工具定义**：定义 AI 可以调用的工具及其参数
2. **工具调用**：AI 根据用户意图选择调用哪个工具
3. **工具执行**：执行工具函数，返回结果
4. **结果整合**：AI 将工具结果整合到回复中

---

## 📄 文件详细说明

### 1. tool_definitions.py - 工具定义

**作用：** 定义所有可供 LLM 调用的工具（OpenAI Function Calling 格式）

**格式：**
```python
TOOL_DEFINITIONS = [
    {
        "type": "function",
        "function": {
            "name": "工具名称",
            "description": "工具描述（AI 会根据这个判断是否调用）",
            "parameters": {
                "type": "object",
                "properties": {
                    "参数名": {
                        "type": "参数类型",
                        "description": "参数描述"
                    }
                },
                "required": ["必需参数列表"]
            }
        }
    }
]
```

**定义的工具：**

#### 1. get_student_quiz_history
获取学生最近的测验历史记录

**参数：**
- `student_id`（必需）：学生 ID
- `limit`（可选）：返回记录数量，默认 5

**用途：** AI 查询学生的练习历史，了解学习情况

#### 2. search_course_content
从课程内容的向量数据库中检索相关知识

**参数：**
- `query`（必需）：搜索关键词或问题描述
- `chapter_id`（可选）：指定章节 ID 过滤
- `top_k`（可选）：返回结果数量，默认 3

**用途：** AI 检索课程内容，获取相关知识用于回答问题

#### 3. get_wrong_questions_by_subsection
获取指定小目标（subsection）的错题记录

**参数：**
- `student_id`（必需）：学生 ID
- `subsection_id`（必需）：小目标 ID
- `limit`（可选）：返回错题数量，默认 5

**用途：** AI 分析学生的薄弱点，针对性出题

#### 4. get_student_learning_progress
获取学生当前的学习进度

**参数：**
- `student_id`（必需）：学生 ID

**用途：** AI 了解学生当前学习到哪里，提供个性化建议

#### 5. get_next_content
获取学生下一阶段的学习内容

**参数：**
- `student_id`（可选）：学生 ID
- `current_subsection_id`（可选）：当前刚完成的小目标 ID

**用途：** AI 推荐下一步学习内容

#### 6. get_student_weak_points
分析学生的薄弱点

**参数：**
- `student_id`（必需）：学生 ID

**用途：** AI 分析学生薄弱环节，提供针对性建议

#### 7. generate_interactive_quiz
根据用户主题生成互动练习题

**参数：**
- `topic`（必需）：用户的主题或提示词
- `count`（可选）：题目数量，默认 3
- `quiz_type`（可选）：题型（mixed/choice/blank 等），默认 mixed
- `difficulty`（可选）：难度（easy/intermediate/hard），默认 intermediate
- `student_id`（可选）：学生 ID

**用途：** AI 在对话中根据用户需求生成练习题（智能问答页面的出题功能）

**注意：** 这个工具用于 AI 智能问答页面的出题功能，不是练习中心！

---

### 2. data_tools.py - 数据查询工具

**作用：** 实现数据查询相关的工具函数

**文件大小：** 23KB

**包含的函数：**

#### get_student_quiz_history
```python
def get_student_quiz_history(
    db: Session,
    student_id: int,
    limit: int = 5
) -> List[Dict[str, Any]]:
    """
    获取学生最近的测验历史
    
    返回：
    [
        {
            "id": 123,
            "score": 85.5,
            "context": "Chapter 1 - Section 1 - Subsection 1",
            "time": "2024-03-20T10:30:00"
        },
        ...
    ]
    """
```

**实现逻辑：**
1. 查询 QuizRecord 表
2. 按时间倒序排列
3. 关联章节信息
4. 返回格式化结果

#### search_course_content
```python
def search_course_content(
    query: str,
    chapter_id: Optional[int] = None,
    top_k: int = 3
) -> List[Dict[str, Any]]:
    """
    检索课程内容向量数据库
    
    返回：
    [
        {
            "content": "文档内容...",
            "title": "文档标题",
            "doc_type": "pdf",
            "relevance": 0.85
        },
        ...
    ]
    """
```

**实现逻辑：**
1. 调用 RAG Service 的 search 方法
2. 在 ChromaDB 中进行语义检索
3. 返回相关文档片段

#### get_wrong_questions_by_subsection
```python
def get_wrong_questions_by_subsection(
    db: Session,
    student_id: int,
    subsection_id: int,
    limit: int = 5
) -> List[Dict[str, Any]]:
    """
    获取指定小目标的错题记录
    
    返回：
    [
        {
            "id": 456,
            "question_type": "choice",
            "retry_count": 3,
            "last_retry_time": "2024-03-20T10:30:00"
        },
        ...
    ]
    """
```

**实现逻辑：**
1. 查询 WrongQuestion 表
2. 筛选指定学生和小目标
3. 按重做次数倒序排列
4. 返回错题信息

#### get_student_learning_progress
```python
def get_student_learning_progress(
    db: Session,
    student_id: int
) -> Dict[str, Any]:
    """
    获取学生当前的学习进度
    
    返回：
    {
        "current_chapter": "Chapter 1",
        "current_section": "Section 1",
        "current_subsection": "Subsection 1",
        "progress_percentage": 45.5
    }
    """
```

**实现逻辑：**
1. 查询学生最近的练习记录
2. 确定当前学习位置
3. 计算整体进度百分比
4. 返回进度信息

#### get_next_content
```python
def get_next_content(
    db: Session,
    student_id: Optional[int] = None,
    current_subsection_id: Optional[int] = None
) -> Dict[str, Any]:
    """
    获取学生下一阶段的学习内容
    
    返回：
    {
        "next_subsection": {
            "id": 10,
            "title": "Subsection 2",
            "content": "..."
        },
        "recommendation": "继续学习下一个知识点"
    }
    """
```

**实现逻辑：**
1. 根据当前小目标 ID 查找下一个
2. 如果没有指定，根据学生进度自动查找
3. 返回下一个学习内容

#### get_student_weak_points
```python
def get_student_weak_points(
    db: Session,
    student_id: int
) -> List[Dict[str, Any]]:
    """
    分析学生的薄弱点
    
    返回：
    [
        {
            "subsection_id": 5,
            "subsection_title": "Grammar - Tenses",
            "avg_score": 45.2,
            "wrong_count": 8
        },
        ...
    ]
    """
```

**实现逻辑：**
1. 查询学生的所有练习记录
2. 按小目标分组统计平均分
3. 筛选平均分最低的几个
4. 返回薄弱点列表

---

### 3. quiz_tools.py - 练习生成工具

**作用：** 实现练习生成相关的工具函数

**文件大小：** 4.4KB

**包含的函数：**

#### generate_interactive_quiz
```python
def generate_interactive_quiz(
    db: Session,
    topic: str,
    count: int = 3,
    quiz_type: str = "mixed",
    difficulty: str = "intermediate",
    student_id: Optional[int] = None
) -> Dict[str, Any]:
    """
    根据用户的主题或提示词生成互动练习题
    
    返回：
    {
        "generate_interactive_quiz_response": {
            "count": 3,
            "questions": [...],
            "topic": "Grammar - Tenses",
            "quiz_id": 0,
            "quiz_type": "mixed",
            "difficulty": "intermediate"
        }
    }
    """
```

**实现流程：**

```
1. 解析主题
   ↓
2. 检查是否有章节引用（如【参考：...】）
   ↓
3. RAG 检索相关内容
   - 优先精确匹配小目标
   - 否则进行语义检索
   ↓
4. 调用 LLM Service 生成题目
   ↓
5. 返回格式化结果
```

**关键特性：**
- 支持章节引用（前端注入）
- 自动 RAG 检索上下文
- 支持多种题型和难度
- 错误处理和降级

---

## 🔧 使用指南

### 在 LLM Service 中使用

```python
from app.tools.tool_definitions import TOOL_DEFINITIONS
from app.tools import (
    get_wrong_questions_by_subsection,
    get_student_learning_progress,
    get_next_content,
    get_student_weak_points,
    get_student_quiz_history,
    search_course_content
)

# 1. 将工具定义传递给 LLM
response = client.chat.completions.create(
    model="gpt-4",
    messages=messages,
    tools=TOOL_DEFINITIONS,  # 传递工具定义
    tool_choice="auto"
)

# 2. 检查是否需要调用工具
if response.choices[0].message.tool_calls:
    tool_call = response.choices[0].message.tool_calls[0]
    function_name = tool_call.function.name
    arguments = json.loads(tool_call.function.arguments)
    
    # 3. 执行工具
    if function_name == "get_student_quiz_history":
        result = get_student_quiz_history(
            db=db,
            student_id=arguments["student_id"],
            limit=arguments.get("limit", 5)
        )
    
    # 4. 将结果返回给 LLM
    messages.append({
        "role": "tool",
        "name": function_name,
        "content": json.dumps(result)
    })
```

---

## 📊 工具分类

### 数据查询工具（data_tools.py）

| 工具名称 | 功能 | 数据源 |
|---------|------|--------|
| get_student_quiz_history | 查询练习历史 | QuizRecord 表 |
| search_course_content | 检索课程内容 | ChromaDB |
| get_wrong_questions_by_subsection | 查询错题 | WrongQuestion 表 |
| get_student_learning_progress | 查询学习进度 | QuizRecord 表 |
| get_next_content | 获取下一内容 | SubSection 表 |
| get_student_weak_points | 分析薄弱点 | QuizRecord 表 |

### 练习生成工具（quiz_tools.py）

| 工具名称 | 功能 | 依赖服务 |
|---------|------|---------|
| generate_interactive_quiz | 生成练习题 | RAG Service, LLM Service |

---

## 🎯 设计原则

### 1. 单一职责

每个工具只负责一个具体功能：
- ✅ `get_student_quiz_history` 只查询历史
- ✅ `search_course_content` 只检索内容
- ❌ 不要在一个工具中混合多个功能

### 2. 清晰的描述

工具描述要清晰明确，让 AI 能准确判断何时调用：
```python
"description": "获取学生最近的测验历史记录，包括分数、涉及的章节等信息。"
```

### 3. 参数验证

必需参数和可选参数要明确区分：
```python
"required": ["student_id"]  # 必需
"limit": {"type": "integer", "description": "可选，默认5"}  # 可选
```

### 4. 错误处理

工具函数应该有完善的错误处理：
```python
try:
    # 执行工具逻辑
    result = ...
    return result
except Exception as e:
    logger.error(f"Tool execution failed: {e}")
    return {"error": str(e)}
```

---

## 📝 工具调用流程

### 完整流程示例

**场景：用户在 AI 智能问答页面提问**

```
用户："我最近的学习情况怎么样？"
    ↓
chat.py API 接收请求
    ↓
llm_service.answer_question() 被调用
    ↓
LLM 分析意图，决定调用工具：get_student_quiz_history
    ↓
LLM 生成工具调用：
{
    "name": "get_student_quiz_history",
    "arguments": {"student_id": 123, "limit": 5}
}
    ↓
后端执行工具函数（data_tools.py）
    ↓
返回结果：
[
    {"score": 85, "context": "Chapter 1 - Section 1", "time": "..."},
    {"score": 72, "context": "Chapter 1 - Section 2", "time": "..."},
    ...
]
    ↓
LLM 整合结果生成回复：
"根据您最近的练习记录，您在 Chapter 1 的表现不错，
平均分 78.5 分。建议继续巩固 Section 2 的内容。"
    ↓
返回给前端显示
```

**对比：练习中心的流程（不使用 Tools）**

```
用户在练习中心点击"开始练习"
    ↓
quiz.py API 接收请求
    ↓
QuizService.create_quiz() 被调用
    ↓
直接调用 LLMService.generate_quiz()
    ↓
生成题目并返回
```

**关键区别：**
- AI 智能问答：使用 Tools（工具调用）
- 练习中心：直接调用 Service（不使用 Tools）

---

## 🔄 与其他层的关系

```
Tools 层
    ↓ 调用
Services 层（业务逻辑）
    ├── RAG Service（向量检索）
    ├── LLM Service（题目生成）
    └── Quiz Service（练习管理）
    ↓ 调用
Models 层（数据模型）
    ├── QuizRecord（练习记录）
    ├── WrongQuestion（错题）
    └── SubSection（小目标）
```

---

## 📊 统计信息

| 文件 | 大小 | 函数数 | 用途 |
|------|------|--------|------|
| tool_definitions.py | 6KB | 7 个工具定义 | 工具定义 |
| data_tools.py | 23KB | 6 个函数 | 数据查询 |
| quiz_tools.py | 4.4KB | 1 个函数 | 练习生成 |

**总计：** 3 个文件，约 33KB 代码，7 个工具

---

## 🎯 最佳实践

### 1. 工具命名

使用清晰、描述性的名称：
- ✅ `get_student_quiz_history`
- ✅ `search_course_content`
- ❌ `get_data`
- ❌ `search`

### 2. 参数设计

参数要足够详细，但不要过度：
```python
# ✅ 好的设计
"student_id": {"type": "integer", "description": "学生的用户ID"}
"limit": {"type": "integer", "description": "返回记录数量限制，默认为5"}

# ❌ 过度设计
"student_id": {
    "type": "integer",
    "description": "学生的用户ID，必须是正整数，范围1-1000000",
    "minimum": 1,
    "maximum": 1000000
}
```

### 3. 返回值设计

返回值要结构化，便于 AI 理解：
```python
# ✅ 好的设计
{
    "id": 123,
    "score": 85.5,
    "context": "Chapter 1 - Section 1",
    "time": "2024-03-20T10:30:00"
}

# ❌ 不好的设计
"123, 85.5, Chapter 1 - Section 1, 2024-03-20T10:30:00"
```

---

## 📚 相关文档

- [OpenAI Function Calling](https://platform.openai.com/docs/guides/function-calling)
- [LangChain Tools](https://python.langchain.com/docs/modules/tools/)

---

**最后更新：** 2026-03-26
**维护人员：** 工具架构师
