# MCP Server 使用指南

## 🎉 MCP Server 创建完成！

### 📁 目录结构

```
backend/mcp_server/
├── server.py              # MCP Server 主程序
├── config.py              # 配置文件
├── requirements.txt       # Python 依赖
├── test_server.py         # 测试脚本
├── start.bat              # Windows 启动脚本
├── start.sh               # Linux/Mac 启动脚本
├── mcp_config.json        # MCP 客户端配置
├── .env.example           # 环境变量模板
└── README.md              # 详细文档
```

## 🚀 快速启动

### 步骤 1: 安装依赖

```bash
cd backend/mcp_server
pip install -r requirements.txt
```

依赖包：
- `mcp>=1.0.0` - MCP SDK
- `PyMySQL>=1.1.0` - MySQL 连接器
- `python-dotenv>=1.0.0` - 环境变量管理
- `pydantic>=2.0.0` - 数据验证
- `pydantic-settings>=2.0.0` - 配置管理

### 步骤 2: 配置数据库

在 `config.py` 中，已经预设了数据库连接：

```python
DATABASE_URL = "mysql+pymysql://root:abc12345@localhost:3306/college_english"
```

或者创建 `.env` 文件覆盖配置：

```bash
# 复制模板
cp .env.example .env

# 编辑 .env 文件
DATABASE_URL=mysql+pymysql://你的用户名:你的密码@localhost:3306/college_english
```

### 步骤 3: 测试工具

运行测试脚本验证功能：

```bash
python test_server.py
```

预期输出：
```
🚀 开始测试 MCP Server 工具...
✅ 数据库连接成功

========================================================
测试 1: fetch_learning_data
========================================================
✅ 成功获取 5 条练习记录

最近一次练习：
  - 章节: Unit 2 情态动词
  - 类型: reading
  - 分数: 45.0
  - 正确率: 40.0%

... (更多测试输出)
```

### 步骤 4: 启动 MCP Server

**Windows:**
```bash
start.bat
```

**Linux/Mac:**
```bash
chmod +x start.sh
./start.sh
```

**或直接运行：**
```bash
python server.py
```

服务启动后会监听 stdio，等待 MCP 客户端连接。

## 🔧 三大工具说明

### 1. fetch_learning_data (获取练习记录)

**功能：** 从数据库查询学生的历史练习记录

**参数：**
- `student_id` (int, 必需) - 学生用户 ID
- `limit` (int, 可选, 默认 50) - 返回记录数量
- `chapter_id` (int, 可选) - 筛选特定章节

**返回数据：**
```json
{
  "student_id": 1,
  "total_records": 5,
  "records": [
    {
      "quiz_id": 10,
      "chapter_id": 2,
      "chapter_title": "情态动词",
      "quiz_type": "reading",
      "question_count": 5,
      "score": 45.0,
      "accuracy": 40.0,
      "time_spent": 180,
      "knowledge_points": ["modal_verbs"],
      "completed_at": "2024-05-03T10:30:00"
    }
  ]
}
```

**AI 使用场景：**
- 分析学生整体学习趋势
- 识别哪些章节掌握较好/较差
- 发现学习习惯（如做题时间、正确率变化）

### 2. fetch_wrong_questions (获取错题记录)

**功能：** 查询学生做错的题目详情

**参数：**
- `student_id` (int, 必需) - 学生用户 ID
- `limit` (int, 可选, 默认 30) - 返回记录数量
- `chapter_id` (int, 可选) - 筛选特定章节
- `is_mastered` (bool, 可选) - 是否只看未掌握的错题

**返回数据：**
```json
{
  "student_id": 1,
  "total_wrong_questions": 8,
  "wrong_questions": [
    {
      "wrong_question_id": 5,
      "chapter_id": 2,
      "chapter_title": "情态动词",
      "question_type": "reading",
      "question_data": {
        "passage": "...",
        "question": "...",
        "options": {...}
      },
      "user_answer": "A",
      "correct_answer": "B",
      "score": 0.0,
      "knowledge_points": ["modal_verbs", "grammar"],
      "is_mastered": false,
      "retry_count": 2,
      "created_at": "2024-05-02T15:20:00"
    }
  ]
}
```

**AI 使用场景：**
- 分析学生常错的题型
- 查看具体错在哪里
- 判断是否需要重做某些题目

### 3. fetch_weak_knowledge_points (薄弱点统计)

**功能：** 统计学生最薄弱的知识点

**参数：**
- `student_id` (int, 必需) - 学生用户 ID
- `top_k` (int, 可选, 默认 5) - 返回前 K 个薄弱点

**返回数据：**
```json
{
  "student_id": 1,
  "total_weak_points": 3,
  "weak_knowledge_points": [
    {
      "knowledge_point_id": "modal_verbs",
      "error_count": 8,
      "related_chapters": [2, 3],
      "question_types": ["reading", "translation"]
    },
    {
      "knowledge_point_id": "past_perfect",
      "error_count": 5,
      "related_chapters": [1],
      "question_types": ["reading"]
    }
  ]
}
```

**AI 使用场景：**
- **精准定位薄弱点**：快速找到学生最需要强化的知识点
- **针对性出题**：为错误最多的知识点生成专项练习
- **生成复习计划**：优先复习错误次数多的知识点

## 💡 AI 分析示例

### 场景：学生请求"帮我分析一下学习情况"

**1. AI 调用 fetch_learning_data:**

```json
{
  "student_id": 1,
  "limit": 20
}
```

**2. AI 调用 fetch_weak_knowledge_points:**

```json
{
  "student_id": 1,
  "top_k": 5
}
```

**3. AI 分析并回复：**

```
根据你最近的学习数据：

📊 整体表现：
- 完成了 15 次练习
- 平均分: 67.5 分
- 最近一周有进步趋势

🎯 薄弱知识点：
1. **情态动词** (8次错误) ⚠️ 重点关注
   - 主要出现在: Unit 2, Unit 3
   - 错误题型: 阅读理解、翻译

2. **虚拟语气** (5次错误)
   - 主要出现在: Unit 1

📝 建议：
我发现你在情态动词方面掌握不太牢固，这是非常重要的语法点。
让我为你生成 5 道情态动词专项练习题，帮你强化这个知识点...

(调用出题 API 生成针对性题目)
```

## 🔌 与主业务后端集成

### 方式 1: 通过 MCP 客户端集成

在主业务后端的 LLM 服务中配置 MCP 客户端：

```python
# backend/app/services/llm_service.py

from langchain.agents import initialize_agent
from langchain_community.tools import MCPTool

# 配置 MCP 工具
mcp_tools = [
    MCPTool(
        server="student-analytics",
        tool="fetch_learning_data"
    ),
    # ...
]

# 创建 Agent
agent = initialize_agent(
    tools=mcp_tools,
    llm=llm,
    agent="openai-functions"
)
```

### 方式 2: 直接在 Prompt 中使用

```python
system_prompt = """
你是一个专业的英语私教。当学生要求分析学习情况时：

1. 使用 fetch_learning_data 工具获取历史记录
2. 使用 fetch_weak_knowledge_points 工具获取薄弱点
3. 根据数据分析学生的强弱项
4. 为薄弱点生成针对性练习

可用工具：
- fetch_learning_data: 获取练习记录
- fetch_weak_knowledge_points: 获取薄弱知识点
- fetch_wrong_questions: 获取错题详情
"""
```

## 📊 数据流程图

```
┌─────────────────┐
│   学生做题      │
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│  MySQL 数据库   │ ← quiz_records
│                 │ ← wrong_questions
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│   MCP Server    │ ← fetch_learning_data
│  (数据桥梁)     │ ← fetch_wrong_questions
│                 │ ← fetch_weak_knowledge_points
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│   LLM (AI 大脑) │
│   深度分析      │ → "你在Unit 2连续两次不及格..."
│   推理决策      │ → "需要强化情态动词..."
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│  生成针对性题目 │
│  或复习计划     │
└─────────────────┘
```

## 🎓 核心设计理念

根据开发文档要求，MCP Server 遵循以下原则：

✅ **只做数据搬运** - 不做业务逻辑，不做数据分析
✅ **原始数据优先** - 让 LLM 自己阅读和分析数据
✅ **灵活筛选** - 支持按章节、时间、状态等多维度筛选
✅ **标准格式** - 返回清晰的 JSON 格式，便于 LLM 理解

## 🔍 调试技巧

### 1. 查看日志

MCP Server 会输出详细的日志信息：

```
2024-05-10 10:00:00 - __main__ - INFO - Starting MCP Server
2024-05-10 10:00:01 - __main__ - INFO - Database connected successfully
2024-05-10 10:00:05 - __main__ - INFO - Fetching learning data for student 1
2024-05-10 10:00:06 - __main__ - INFO - Retrieved 10 learning records
```

### 2. 使用测试脚本

```bash
python test_server.py
```

### 3. 手动测试工具

```python
import asyncio
from server import fetch_learning_data, db

async def test():
    db.connect()
    result = await fetch_learning_data({"student_id": 1})
    print(result[0].text)
    db.close()

asyncio.run(test())
```

## ⚠️ 常见问题

### Q1: 数据库连接失败

**现象：** `Database connection failed: (2003, "Can't connect to MySQL server...")`

**解决：**
1. 检查 MySQL 是否启动
2. 验证 `config.py` 中的数据库连接信息
3. 确保防火墙允许 3306 端口

### Q2: 查询返回空数据

**原因：** 数据库中可能没有该学生的记录

**验证：**
```sql
SELECT * FROM quiz_records WHERE user_id = 1 LIMIT 5;
```

### Q3: 工具调用失败

**检查：**
1. 参数是否正确（student_id 必需）
2. 数据类型是否匹配
3. 查看日志了解详细错误

## 📚 下一步

1. **启动 MCP Server**
   ```bash
   python server.py
   ```

2. **在主业务后端集成 MCP 工具**
   - 配置 MCP 客户端
   - 在 AI 对话中使用工具

3. **测试 AI 分析功能**
   - 让学生提问"分析我的学习情况"
   - 观察 AI 如何调用 MCP 工具
   - 验证针对性出题功能

4. **优化和扩展**
   - 根据实际使用调整工具参数
   - 添加更多分析维度
   - 优化查询性能

## 🎉 完成！

MCP Server 已经准备就绪，可以为 AI 提供强大的学情数据支持，实现真正的智能化、个性化教学！
