# 启动模式说明

## 📋 两种启动模式

本项目支持两种启动模式，代码完全隔离，互不影响。

---

## 🚀 启动命令

### 1. 默认模式（原工具调用）

```bash
# 方式1：直接运行
python -m app.main

# 方式2：使用 uvicorn
uvicorn app.main:app --host 0.0.0.0 --port 8000
```

**特点：**
- ✅ 使用原工具代码（`app/tools/`）
- ✅ 直接调用本地函数
- ✅ 支持降级保护
- ✅ 性能最优

**加载的服务：**
- `app.services.llm_service.llm_service`
- `app.services.orchestrator.orchestrator`

---

### 2. MCP 模式（MCP 服务调用）

```bash
# 方式1：添加 mcp 参数
python -m app.main mcp

# 方式2：使用 uvicorn（需要先设置环境变量）
export MCP_MODE=true
uvicorn app.main:app --host 0.0.0.0 --port 8000
```

**特点：**
- ✅ 使用 MCP 服务（`mcp_server/`）
- ✅ 通过 MCP 协议调用工具
- ✅ 独立进程运行
- ✅ 满足毕设要求

**加载的服务：**
- `app.services.mcp_llm_service.mcp_llm_service`
- `app.services.mcp_orchestrator.mcp_orchestrator`

---

## 📊 文件结构

### 默认模式文件

```
app/services/
├── llm_service.py              # 原LLM服务
├── orchestrator.py             # 原编排层
└── ...

app/tools/
├── data_tools.py               # 原数据工具
├── quiz_tools.py               # 原练习工具
└── tool_definitions.py         # 原工具定义
```

### MCP 模式文件

```
app/services/
├── mcp_llm_service.py          # MCP LLM服务
├── mcp_orchestrator.py         # MCP 编排层
├── mcp_tool_definitions.py     # MCP 工具定义
└── ...

mcp_server/
└── server.py                   # MCP 服务主程序
```

---

## 🔧 代码隔离

### 完全隔离的设计

**默认模式：**
- 文件：`llm_service.py`, `orchestrator.py`
- 工具：`app/tools/`
- 调用：直接调用本地函数

**MCP 模式：**
- 文件：`mcp_llm_service.py`, `mcp_orchestrator.py`
- 工具：`mcp_server/server.py`
- 调用：通过 MCP 协议

**互不影响：**
- ✅ 文件完全分开
- ✅ 代码不复用
- ✅ 逻辑独立
- ✅ 可以单独测试

---

## 🧪 测试验证

### 测试默认模式

```bash
# 启动
python -m app.main

# 检查健康状态
curl http://localhost:8000/health

# 预期输出
{
  "status": "healthy",
  "mode": "DEFAULT",
  ...
}
```

### 测试 MCP 模式

```bash
# 启动
python -m app.main mcp

# 检查健康状态
curl http://localhost:8000/health

# 预期输出
{
  "status": "healthy",
  "mode": "MCP",
  ...
}
```

---

## 📝 日志输出

### 默认模式日志

```
Starting in DEFAULT mode
Loading default services...
Default LLM Service loaded
College English Assistant started successfully in DEFAULT mode!
```

### MCP 模式日志

```
Starting in MCP mode
Loading MCP services...
MCP LLM Service loaded
College English Assistant started successfully in MCP mode!
```

---

## 🎯 使用建议

### 开发和调试

**推荐：默认模式**
- 性能更好
- 调试更方便
- 错误更直观

### 毕设演示

**推荐：MCP 模式**
- 满足毕设要求
- 展示 MCP 架构
- 体现技术深度

### 生产环境

**推荐：默认模式**
- 性能最优
- 稳定性最好
- 维护最简单

---

## 🔄 切换模式

切换模式只需修改启动命令：

```bash
# 默认模式
python -m app.main

# MCP 模式
python -m app.main mcp
```

**无需修改任何代码！**

---

## 📚 相关文档

- [MCP 服务文档](./mcp_server/README.md)
- [实现总结](./MCP_IMPLEMENTATION.md)

---

**最后更新：** 2026-03-26
