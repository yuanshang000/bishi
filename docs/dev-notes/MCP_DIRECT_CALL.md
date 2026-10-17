# MCP 直接调用模式说明

## 🐛 问题原因

之前的 MCP Orchestrator 使用 `stdio_client` 通过标准输入输出与 MCP Server 通信，这种方式：
- 在 Windows 上不稳定
- 需要启动子进程
- 调试困难
- 容易出错

---

## ✅ 解决方案

改为**直接调用模式**：
- MCP Orchestrator 直接调用 MCP Server 的函数
- 不通过 stdio 协议
- 不需要启动子进程
- 更简单、更可靠

---

## 📊 架构对比

### 之前的方式（stdio）

```
主应用
  ↓
MCP Orchestrator
  ↓
stdio_client (启动子进程)
  ↓
MCP Server (子进程)
  ↓
工具执行
```

**问题：**
- 需要进程间通信
- Windows 兼容性差
- 复杂度高

### 现在的方式（直接调用）

```
主应用
  ↓
MCP Orchestrator
  ↓
直接调用 handle_tool_call()
  ↓
MCP Server (函数调用)
  ↓
工具执行
```

**优点：**
- 无需进程间通信
- 跨平台兼容
- 简单可靠
- 易于调试

---

## 🔧 实现细节

### 1. MCP Server 添加直接调用接口

**文件：** `mcp_server/server.py`

```python
def handle_tool_call(name: str, arguments: Dict[str, Any]) -> Any:
    """
    直接调用工具（不通过 MCP 协议）
    用于 MCP Orchestrator 直接调用
    """
    logger.info(f"MCP Server direct tool call: {name}")
    
    # 创建数据库会话
    db = SessionLocal()
    
    try:
        # 根据工具名称调用对应的实现函数
        if name == "get_student_learning_progress":
            result = _get_student_learning_progress(
                db=db,
                student_id=arguments["student_id"]
            )
        # ... 其他工具
        
        return result
    finally:
        db.close()
```

### 2. MCP Orchestrator 直接调用

**文件：** `app/services/mcp_orchestrator.py`

```python
def _call_mcp_tool_direct(self, tool_name: str, arguments: Dict[str, Any]) -> Any:
    """直接调用 MCP Server 的工具函数"""
    # 导入 MCP Server 的工具处理函数
    from mcp_server.server import handle_tool_call
    
    # 直接调用工具
    result = handle_tool_call(tool_name, arguments)
    
    return result
```

---

## 🎯 优势

### 1. 简化架构

**之前：** 主应用 → Orchestrator → stdio → MCP Server → 工具
**现在：** 主应用 → Orchestrator → MCP Server → 工具

### 2. 提高可靠性

- ✅ 无进程间通信
- ✅ 无子进程管理
- ✅ 无 stdio 协议
- ✅ 跨平台兼容

### 3. 易于调试

- 所有代码在同一进程
- 可以直接设置断点
- 日志更清晰
- 错误更容易追踪

### 4. 性能更好

- 无进程启动开销
- 无序列化/反序列化
- 无 IPC 延迟

---

## 🧪 测试方法

### 1. 启动 MCP 模式

```bash
cd backend
python -m app.main mcp
```

**注意：** 现在不需要单独启动 MCP Server！

### 2. 发送请求

发送聊天请求，应该看到：

```
MCP Orchestrator executing tool: get_student_learning_progress
Calling MCP tool directly: get_student_learning_progress
MCP Server direct tool call: get_student_learning_progress
MCP Server direct tool call successful
Tool get_student_learning_progress executed successfully via MCP
```

---

## 📝 启动方式变化

### 之前

```bash
# 终端 1：启动 MCP Server
python mcp_server/server.py

# 终端 2：启动主应用
python -m app.main mcp
```

### 现在

```bash
# 只需要启动主应用
python -m app.main mcp
```

**MCP Server 不需要单独启动！**

---

## 🔄 兼容性

### MCP 协议仍然支持

- MCP Server 仍然实现了完整的 MCP 协议
- 可以通过 stdio 方式调用（如果需要）
- `handle_tool_call()` 是额外的直接调用接口

### 两种调用方式

**方式 1：MCP 协议（stdio）**
```python
# 通过 MCP Client 调用
async with stdio_client(server_params) as (read, write):
    client = Client("mcp-orchestrator")
    await client.connect(read, write)
    result = await client.call_tool(tool_name, arguments)
```

**方式 2：直接调用**
```python
# 直接调用函数
from mcp_server.server import handle_tool_call
result = handle_tool_call(tool_name, arguments)
```

---

## 💡 总结

**改进：**
- 从 stdio 进程间通信改为直接函数调用
- 简化架构，提高可靠性
- 更容易调试和维护

**启动：**
- 只需要启动主应用
- 不需要单独启动 MCP Server

**测试：**
```bash
python -m app.main mcp
```

现在 MCP 模式应该可以正常工作了！

---

**最后更新：** 2026-03-26
