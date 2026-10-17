# MCP 模式修复说明

## 🐛 问题原因

启动 MCP 模式后，API 路由仍然使用原来的 `llm_service`，没有根据启动模式选择正确的服务。

---

## ✅ 已修复的文件

### 1. `app/api/v1/chat.py`

**修改前：**
```python
from app.services.llm_service import llm_service
```

**修改后：**
```python
# 根据启动模式选择 LLM 服务
MCP_MODE = "mcp" in sys.argv
if MCP_MODE:
    from app.services.mcp_llm_service import mcp_llm_service as llm_service
else:
    from app.services.llm_service import llm_service
```

### 2. `app/services/quiz_service.py`

**修改：** 同样的模式选择逻辑

### 3. `app/tools/quiz_tools.py`

**修改：** 在函数内部根据模式选择服务

### 4. `app/services/course_parser.py`

**修改：** 在 `__init__` 方法中根据模式选择服务

---

## 🔄 工作原理

### 启动模式检测

```python
MCP_MODE = "mcp" in sys.argv
```

- 如果启动命令包含 `mcp` 参数，则 `MCP_MODE = True`
- 否则 `MCP_MODE = False`

### 服务选择

**默认模式：**
```python
from app.services.llm_service import llm_service
```
- 使用原 LLM 服务
- 直接调用本地工具函数

**MCP 模式：**
```python
from app.services.mcp_llm_service import mcp_llm_service as llm_service
```
- 使用 MCP LLM 服务
- 通过 MCP 协议调用工具

---

## 🧪 验证方法

### 1. 启动 MCP 模式

```bash
cd backend
start_mcp.bat
```

### 2. 检查日志

**预期日志：**
```
Starting in MCP mode
Loading MCP services...
MCP LLM Service loaded
```

### 3. 发送请求

发送聊天请求后，应该看到：
- MCP Orchestrator 连接 MCP Server
- MCP Server 执行工具
- 返回结果

---

## 📊 调用流程对比

### 默认模式流程

```
用户请求
  ↓
API 路由
  ↓
llm_service (原)
  ↓
orchestrator (原)
  ↓
直接调用本地工具函数
  ↓
返回结果
```

### MCP 模式流程

```
用户请求
  ↓
API 路由
  ↓
mcp_llm_service (MCP)
  ↓
mcp_orchestrator (MCP)
  ↓
通过 stdio 连接 MCP Server
  ↓
MCP Server 执行工具
  ↓
返回结果
```

---

## 🎯 现在可以正常使用 MCP 模式了

重新启动服务：

```bash
cd backend
start_mcp.bat
```

现在发送请求应该会走 MCP 路线了！

---

**最后更新：** 2026-03-26
