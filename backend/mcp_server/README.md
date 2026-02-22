# MCP Server - Student Learning Analytics

## 📋 简介

这是一个基于 Model Context Protocol (MCP) 的服务，专门用于提供学生学情数据给 AI 进行分析。

### 核心功能

MCP Server 作为数据桥梁，从数据库中提取学生的学习数据，供 LLM 进行薄弱点分析和针对性出题。

**三大工具：**

1. **`fetch_learning_data`** - 获取学生的历史练习记录
   - 输入：student_id, limit (可选), chapter_id (可选)
   - 输出：章节、题型、分数、正确率、用时等数据

2. **`fetch_wrong_questions`** - 获取学生的错题记录
   - 输入：student_id, limit (可选), chapter_id (可选), is_mastered (可选)
   - 输出：错题内容、用户答案、正确答案、知识点等

3. **`fetch_weak_knowledge_points`** - 统计薄弱知识点
   - 输入：student_id, top_k (可选)
   - 输出：错误次数最多的知识点及其统计信息

## 🚀 快速开始

### 1. 安装依赖

```bash
pip install -r requirements.txt
```

### 2. 配置数据库

编辑 `config.py`，修改数据库连接字符串：

```python
DATABASE_URL = "mysql+pymysql://用户名:密码@主机:端口/数据库名"
```

或者创建 `.env` 文件：

```env
DATABASE_URL=mysql+pymysql://root:abc12345@localhost:3306/college_english
```

### 3. 启动服务

**Windows:**
```bash
start.bat
```

**Linux/Mac:**
```bash
chmod +x start.sh
./start.sh
```

**或直接运行:**
```bash
python server.py
```

## 📊 工具使用示例

### 示例 1: 获取学生练习记录

```json
{
  "name": "fetch_learning_data",
  "arguments": {
    "student_id": 1,
    "limit": 20,
    "chapter_id": 2
  }
}
```

**返回数据示例:**
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
      "knowledge_points": ["modal_verbs", "grammar"],
      "completed_at": "2024-05-03T10:30:00"
    }
  ]
}
```

### 示例 2: 获取错题记录

```json
{
  "name": "fetch_wrong_questions",
  "arguments": {
    "student_id": 1,
    "is_mastered": false
  }
}
```

### 示例 3: 获取薄弱知识点

```json
{
  "name": "fetch_weak_knowledge_points",
  "arguments": {
    "student_id": 1,
    "top_k": 5
  }
}
```

**返回数据示例:**
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
    }
  ]
}
```

## 🎯 设计理念

根据开发文档的要求，MCP Server 遵循以下原则：

1. **只负责数据搬运** - 不做业务逻辑，不做统计计算
2. **原始数据优先** - 返回数据库中的原始记录，让 LLM 自己分析
3. **支持灵活筛选** - 支持按章节、时间、掌握状态等筛选
4. **格式化输出** - 将数据清洗成易于 LLM 理解的 JSON 格式

## 🔌 与主业务后端集成

MCP Server 作为独立进程运行，主业务后端（FastAPI）通过 MCP 协议调用其提供的工具。

AI 分析流程：
```
用户提问 "帮我复习一下"
    ↓
LLM 判断需要数据，调用 fetch_learning_data
    ↓
MCP Server 从 MySQL 查询数据
    ↓
返回原始数据给 LLM
    ↓
LLM 深度分析："你在 Unit 2 连续两次不及格..."
    ↓
LLM 生成针对性题目或复习计划
```

## 📝 数据来源

### 主要数据表

1. **quiz_records** - 练习记录表
   - 字段：user_id, chapter_id, quiz_type, score, accuracy, time_spent, questions, user_answers, knowledge_point_ids 等

2. **wrong_questions** - 错题记录表
   - 字段：user_id, chapter_id, question_type, question_data, user_answer, correct_answer, knowledge_point_ids, is_mastered, retry_count 等

3. **chapters** - 章节表
   - 用于关联章节信息

## 🛠️ 开发与调试

### 查看日志

服务器运行时会输出详细日志：

```
2024-05-10 10:00:00 - __main__ - INFO - Starting MCP Server: student-analytics v1.0.0
2024-05-10 10:00:01 - __main__ - INFO - Database connected successfully
2024-05-10 10:00:02 - __main__ - INFO - MCP Server is running on stdio
```

### 测试工具

可以使用 MCP Inspector 或编写测试脚本来测试工具：

```python
# test_mcp.py
import asyncio
from server import fetch_learning_data

async def test():
    result = await fetch_learning_data({"student_id": 1, "limit": 10})
    print(result[0].text)

asyncio.run(test())
```

## 🔒 安全注意事项

1. **数据库凭证** - 不要将数据库密码硬编码，使用环境变量
2. **权限控制** - 确保 MCP Server 只能被授权的 AI 系统调用
3. **数据脱敏** - 如需要，可以在返回数据前进行脱敏处理

## 📚 相关文档

- [MCP 协议规范](https://modelcontextprotocol.io/)
- [开发文档](../开发文档.md)
- [主业务后端 API 文档](../README.md)

## 🙋 FAQ

### Q: MCP Server 是否需要一直运行？
A: 是的，MCP Server 需要作为独立进程持续运行，主业务后端会通过 stdio 或其他方式与其通信。

### Q: 如何添加新的工具？
A: 在 `server.py` 中：
1. 定义参数模型（继承 BaseModel）
2. 在 `list_tools()` 中注册工具
3. 在 `call_tool()` 中添加路由
4. 实现工具函数

### Q: 数据查询性能如何优化？
A:
- 确保数据库表有正确的索引（user_id, chapter_id, created_at）
- 使用 limit 参数限制返回数量
- 考虑添加缓存机制

## 📄 License

本项目为毕业设计项目，仅供学习和参考使用。
