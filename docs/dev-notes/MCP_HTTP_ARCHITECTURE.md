# MCP HTTP API 架构说明

## 🎯 为什么改为 HTTP API

### 之前的问题

**直接调用模式：**
```python
from mcp_server.server import handle_tool_call
result = handle_tool_call(tool_name, arguments)
```

**问题：**
- ❌ 和原来的工具调用没区别
- ❌ 没有体现 MCP 的价值
- ❌ 不是真正的服务分离

---

## ✅ HTTP API 架构

### 架构图

```
┌─────────────────┐         HTTP POST          ┌──────────────────┐
│   主应用         │ ────────────────────────> │  MCP HTTP Server │
│  (Port 8000)    │                            │   (Port 8001)    │
│                 │ <──────────────────────── │                  │
│  FastAPI        │         JSON Response      │  FastAPI         │
└─────────────────┘                            └──────────────────┘
                                                        │
                                                        │
                                                        ↓
                                                 ┌──────────────┐
                                                 │  工具执行     │
                                                 │  数据库访问   │
                                                 └──────────────┘
```

### 核心特点

1. **真正的服务分离**
   - 主应用和 MCP Server 是两个独立的进程
   - 可以独立部署、扩展、维护

2. **标准化接口**
   - 使用 HTTP API 作为通信协议
   - RESTful 风格，易于理解和调试

3. **跨平台兼容**
   - HTTP 协议在所有平台都稳定
   - 不依赖 stdio 或进程间通信

---

## 📊 实现细节

### 1. MCP HTTP Server

**文件：** `mcp_server/http_server.py`

**核心接口：**

```python
POST /call
{
  "name": "get_student_learning_progress",
  "arguments": {
    "student_id": 17
  }
}

Response:
{
  "success": true,
  "result": {
    "recent_quiz": {...},
    "total_wrong_questions": 5
  }
}
```

**其他接口：**
- `GET /` - 服务信息
- `GET /health` - 健康检查
- `GET /tools` - 列出所有工具

### 2. MCP Orchestrator

**文件：** `app/services/mcp_orchestrator.py`

**调用方式：**

```python
# 通过 HTTP 调用 MCP Server
response = httpx.post(
    "http://localhost:8001/call",
    json={
        "name": tool_name,
        "arguments": arguments
    }
)

result = response.json()["result"]
```

---

## 🚀 启动方式

### 方式 1：使用启动脚本（推荐）

```bash
cd backend
start_mcp.bat
```

**启动流程：**
1. 启动 MCP HTTP Server (端口 8001)
2. 等待 3 秒
3. 启动主应用 (端口 8000)

### 方式 2：分别启动（用于调试）

**终端 1 - 启动 MCP HTTP Server：**
```bash
cd backend
python mcp_server/http_server.py
```

**终端 2 - 启动主应用：**
```bash
cd backend
python -m app.main mcp
```

---

## 🧪 测试验证

### 1. 测试 MCP HTTP Server

```bash
# 健康检查
curl http://localhost:8001/health

# 列出工具
curl http://localhost:8001/tools

# 调用工具
curl -X POST http://localhost:8001/call \
  -H "Content-Type: application/json" \
  -d '{
    "name": "get_student_learning_progress",
    "arguments": {"student_id": 17}
  }'
```

### 2. 测试主应用

```bash
# 健康检查
curl http://localhost:8000/health

# 应该看到
{
  "status": "healthy",
  "mode": "MCP",
  ...
}
```

### 3. 测试完整流程

发送聊天请求，查看日志：

```
MCP Orchestrator executing tool: get_student_learning_progress
Calling MCP HTTP API: get_student_learning_progress
Tool get_student_learning_progress executed successfully via MCP HTTP
```

---

## 📝 日志示例

### MCP HTTP Server 日志

```
INFO:     Started server process [12345]
INFO:     Uvicorn running on http://0.0.0.0:8001
INFO:     MCP HTTP Server received tool call: get_student_learning_progress
INFO:     Tool get_student_learning_progress executed successfully
```

### 主应用日志

```
INFO:     Starting in MCP mode
INFO:     Loading MCP services...
INFO:     MCP LLM Service loaded
INFO:     MCP Orchestrator executing tool: get_student_learning_progress
INFO:     Calling MCP HTTP API: get_student_learning_progress
INFO:     Tool get_student_learning_progress executed successfully via MCP HTTP
```

---

## 🔄 与原工具调用的对比

### 原工具调用

```
主应用 → llm_service → orchestrator → 本地工具函数
```

**特点：**
- 单进程
- 直接函数调用
- 性能最优

### MCP HTTP 调用

```
主应用 → mcp_llm_service → mcp_orchestrator → HTTP → MCP Server → 工具函数
```

**特点：**
- 双进程
- HTTP 通信
- 服务分离
- 可独立部署

---

## 💡 MCP 的价值体现

### 1. 服务分离

- ✅ 主应用和工具服务独立运行
- ✅ 可以分别重启、扩展
- ✅ 故障隔离

### 2. 标准化接口

- ✅ HTTP API 标准接口
- ✅ 易于集成和调试
- ✅ 可以用其他语言实现 MCP Server

### 3. 独立部署

- ✅ MCP Server 可以部署到其他服务器
- ✅ 可以有多个 MCP Server 实例
- ✅ 负载均衡

### 4. 满足毕设要求

- ✅ 体现了 MCP 架构
- ✅ 展示了服务分离思想
- ✅ 有技术深度

---

## 🎯 总结

**现在的实现：**
- ✅ 真正的服务分离
- ✅ 标准化 HTTP API
- ✅ 体现 MCP 价值
- ✅ 满足毕设要求

**启动方式：**
```bash
start_mcp.bat
```

**架构：**
- 主应用：端口 8000
- MCP Server：端口 8001
- 通信：HTTP API

---

**最后更新：** 2026-03-26
