# MCP Server - Model Context Protocol 服务

本目录包含完整的 MCP 服务，提供所有工具调用能力。

## 📋 目录结构

```
mcp_server/
├── server.py              # MCP 服务主程序（包含所有工具）
├── requirements.txt       # MCP 服务依赖
└── README.md              # 本文档
```

## 🎯 核心作用

**MCP（Model Context Protocol）服务是一个独立的进程，通过标准化的协议提供所有工具调用能力。**

### 为什么所有工具都可以迁移？

1. ✅ MCP 服务和主应用使用**同一个数据库**
2. ✅ MCP 服务可以导入和使用 ORM 模型
3. ✅ MCP 服务可以创建自己的数据库会话
4. ✅ 所有工具都可以在 MCP 服务中实现

---

## 🏗️ 架构设计

### 完整 MCP 架构

```
┌─────────────────────────────────────────┐
│         AI 智能问答页面                  │
└──────────────┬──────────────────────────┘
               ↓
┌─────────────────────────────────────────┐
│      LLM Service (answer_question)      │
│    - 接收用户问题                        │
│    - LLM 决定是否调用工具                │
└──────────────┬──────────────────────────┘
               ↓
┌─────────────────────────────────────────┐
│      编排层（Orchestrator）              │
│  - 解析工具调用请求                      │
│  - 通过 MCP 协议调用工具                 │
└──────────────┬──────────────────────────┘
               ↓
┌─────────────────────────────────────────┐
│         MCP 服务（独立进程）             │
│  - 所有工具都在这里                      │
│  - 访问数据库、RAG、LLM                  │
│  - 返回结果                              │
└─────────────────────────────────────────┘
```

### 工作流程

```
1. 用户提问："我最近的学习情况怎么样？"
    ↓
2. LLM 分析意图，输出工具调用请求：
   {"tool": "get_student_quiz_history", "params": {"student_id": 123}}
    ↓
3. 编排层解析请求，识别工具名
    ↓
4. 通过 MCP 协议调用 MCP 服务
    ↓
5. MCP 服务执行：
   - 创建数据库会话
   - 查询数据库
   - 返回结果
    ↓
6. 编排层将结果返回给 LLM
    ↓
7. LLM 生成最终回答：
   "根据您最近的练习记录..."
```

---

## 📊 工具列表

### 数据查询工具（5个）

| 工具名称 | 功能 | 数据源 |
|---------|------|--------|
| `get_student_quiz_history` | 查询练习历史 | QuizRecord 表 |
| `get_wrong_questions_by_subsection` | 查询错题 | WrongQuestion 表 |
| `get_student_learning_progress` | 查询学习进度 | QuizRecord 表 |
| `get_next_content` | 获取下一内容 | SubSection 表 |
| `get_student_weak_points` | 分析薄弱点 | QuizRecord 表 |

### 内容检索工具（1个）

| 工具名称 | 功能 | 数据源 |
|---------|------|--------|
| `search_course_content` | 检索课程内容 | ChromaDB |

### 练习生成工具（1个）

| 工具名称 | 功能 | 依赖 |
|---------|------|------|
| `generate_interactive_quiz` | 生成练习题 | RAG + LLM |

### 数据访问工具（3个）

| 工具名称 | 功能 | 数据源 |
|---------|------|--------|
| `fetch_learning_data` | 获取学习数据 | QuizRecord 表 |
| `fetch_wrong_questions` | 获取错题记录 | WrongQuestion 表 |
| `fetch_weak_knowledge_points` | 获取薄弱知识点 | WrongQuestion 表 |

**总计：10 个工具**

---

## 📄 文件说明

### server.py - MCP 服务主程序

**核心组件：**

1. **工具定义**（`list_tools`）
   - 定义所有工具的名称、描述、参数
   - 使用 OpenAI Function Calling 格式

2. **工具执行**（`call_tool`）
   - 接收工具调用请求
   - 创建数据库会话
   - 执行对应工具函数
   - 返回结果

3. **工具实现函数**
   - `_get_student_quiz_history` - 查询练习历史
   - `_get_wrong_questions_by_subsection` - 查询错题
   - `_get_student_learning_progress` - 查询学习进度
   - `_get_next_content` - 获取下一内容
   - `_get_student_weak_points` - 分析薄弱点
   - `_search_course_content` - 检索课程内容
   - `_generate_interactive_quiz` - 生成练习题
   - `_fetch_learning_data` - 获取学习数据
   - `_fetch_wrong_questions` - 获取错题记录
   - `_fetch_weak_knowledge_points` - 获取薄弱知识点

**数据库访问：**

```python
# 创建数据库会话
db = SessionLocal()

try:
    # 执行查询
    records = db.query(QuizRecord).filter(...).all()
    
    # 返回结果
    return result
finally:
    # 关闭会话
    db.close()
```

---

## 🚀 使用方法

### 启动 MCP 服务

```bash
cd backend/mcp_server
python server.py
```

服务将通过 stdio 协议监听请求。

### 通过编排层调用

```python
from app.services.orchestrator import orchestrator

# 调用任何工具
result = orchestrator.execute_tool(
    tool_name="get_student_quiz_history",
    arguments={"student_id": 123, "limit": 5}
)
```

---

## 🔧 配置说明

### MCP 协议

**使用 stdio 协议：**
- 输入：通过标准输入接收 JSON-RPC 请求
- 输出：通过标准输出返回 JSON-RPC 响应

**优点：**
- ✅ 简单可靠
- ✅ 无需网络配置
- ✅ 易于调试

### 降级策略

**如果 MCP 服务不可用：**
1. 编排层捕获异常
2. 自动降级到本地函数调用
3. 确保功能不中断

```python
try:
    # 尝试 MCP 调用
    result = mcp_call()
except:
    # 降级到本地调用
    result = local_call()
```

---

## 🎯 设计原则

### 1. 完整迁移

所有工具都迁移到 MCP 服务：
- ✅ 数据查询工具
- ✅ 内容检索工具
- ✅ 练习生成工具
- ✅ 数据访问工具

### 2. 数据库访问

MCP 服务直接访问数据库：
```python
from app.core.database import SessionLocal

db = SessionLocal()
records = db.query(QuizRecord).filter(...).all()
db.close()
```

### 3. 服务复用

MCP 服务可以导入和使用主应用的服务：
```python
from app.services.rag_service import rag_service
from app.services.llm_service import llm_service
```

---

## 📝 开发指南

### 添加新的 MCP 工具

1. 在 `list_tools` 中定义工具：
```python
Tool(
    name="new_tool",
    description="新工具描述",
    inputSchema={...}
)
```

2. 在 `call_tool` 中添加分支：
```python
elif name == "new_tool":
    result = _new_tool(**arguments)
```

3. 实现工具函数：
```python
def _new_tool(db, **kwargs):
    # 实现逻辑
    return result
```

---

## 🧪 测试

### 测试 MCP 服务

```bash
# 启动服务
python server.py

# 发送测试请求（通过 stdin）
{"jsonrpc": "2.0", "method": "tools/call", "params": {"name": "get_student_quiz_history", "arguments": {"student_id": 1}}, "id": 1}
```

### 测试编排层

```python
from app.services.orchestrator import orchestrator

result = orchestrator.execute_tool(
    tool_name="get_student_quiz_history",
    arguments={"student_id": 1, "limit": 5}
)
print(result)
```

---

## 📚 相关文档

- [MCP 协议规范](https://modelcontextprotocol.io/)
- [编排层代码](../app/services/orchestrator.py)
- [实现总结](../MCP_IMPLEMENTATION.md)

---

## 🎓 毕设答辩要点

### 1. 为什么所有工具都可以迁移？

**答：**
- MCP 服务和主应用使用同一个数据库
- MCP 服务可以导入 ORM 模型
- MCP 服务可以创建数据库会话
- 所有工具都可以在独立进程中实现

### 2. MCP 服务如何访问数据库？

**答：**
- 导入 `app.core.database.SessionLocal`
- 创建数据库会话
- 使用 SQLAlchemy ORM 查询
- 关闭会话

### 3. 编排层的作用是什么？

**答：**
- 解析 LLM 的工具调用请求
- 通过 MCP 协议调用工具
- 提供降级保护
- 统一的工具调用接口

### 4. 如何保证系统可靠性？

**答：**
- 降级保护：MCP 不可用时自动降级
- 错误处理：完善的异常捕获
- 数据库会话管理：确保资源释放

---

**最后更新：** 2026-03-26
**维护人员：** MCP 架构师
