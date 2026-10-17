# MCP 模式启动指南

## ✅ 问题已解决

MCP Server 现在可以正常启动了！

---

## 🚀 启动方式

### 方式 1：使用启动脚本（推荐）

**Windows:**
```bash
cd backend
start_mcp.bat
```

**Linux/Mac:**
```bash
cd backend
chmod +x start_mcp.sh
./start_mcp.sh
```

### 方式 2：分别启动（用于调试）

**终端 1 - 启动 MCP Server:**
```bash
cd backend
python mcp_server/server.py
```

**终端 2 - 启动主应用:**
```bash
cd backend
python -m app.main mcp
```

---

## 📊 启动流程

### 正常启动顺序

```
1. MCP Server 启动
   ↓
   - 加载配置
   - 初始化数据库连接
   - 注册所有工具
   - 等待连接

2. 主应用启动
   ↓
   - 识别 MCP 模式
   - 加载 MCP LLM Service
   - 连接数据库
   - 开始监听请求

3. 工具调用流程
   ↓
   - 用户提问
   - LLM 决定调用工具
   - MCP Orchestrator 连接 MCP Server
   - MCP Server 执行工具
   - 返回结果
```

---

## 🧪 验证启动

### 测试 MCP Server 导入

```bash
cd backend/mcp_server
python test_imports.py
```

**预期输出:**
```
Testing MCP Server imports...
OK: Database imported
OK: Config imported: College English Assistant
OK: Models imported
OK: RAG Service imported
OK: LLM Service imported

SUCCESS: All imports successful! MCP Server can start properly.
```

### 测试主应用启动

```bash
cd backend
python -m app.main mcp
```

**预期日志:**
```
Starting in MCP mode
Loading MCP services...
MCP LLM Service loaded
College English Assistant started successfully in MCP mode!
```

---

## 📝 启动脚本说明

### start_mcp.bat (Windows)

```batch
@echo off
echo Starting MCP Server and Main Application...

:: 切换到 backend 目录
cd /d "%~dp0"

:: 启动 MCP Server（后台运行）
start /B python mcp_server\server.py
echo MCP Server started

:: 等待 3 秒让 MCP Server 完全启动
timeout /t 3 /nobreak >nul

:: 启动主应用
echo Starting Main Application in MCP mode...
python -m app.main mcp
```

### start_mcp.sh (Linux/Mac)

```bash
#!/bin/bash
echo "Starting MCP Server and Main Application..."

# 启动 MCP Server（后台运行）
python mcp_server/server.py &
echo "MCP Server started"

# 等待 2 秒
sleep 2

# 启动主应用
echo "Starting Main Application in MCP mode..."
python -m app.main mcp
```

---

## 🔧 故障排除

### 问题 1: 找不到环境变量

**错误:**
```
pydantic_core._pydantic_core.ValidationError: 10 validation errors for Settings
DATABASE_URL Field required
```

**解决:**
- 已修复：MCP Server 现在会自动切换到项目根目录
- 确保 `.env` 文件在 `backend/` 目录下

### 问题 2: MCP Server 无法启动

**检查步骤:**
1. 运行测试脚本：`python mcp_server/test_imports.py`
2. 检查 `.env` 文件是否存在
3. 检查数据库连接是否正常

### 问题 3: 工具调用失败

**可能原因:**
- MCP Server 未启动
- MCP Server 启动失败
- 网络连接问题

**解决:**
- 使用启动脚本确保 MCP Server 先启动
- 检查 MCP Server 日志

---

## 💡 使用建议

### 开发调试

**推荐：默认模式**
```bash
python -m app.main
```
- 不需要 MCP Server
- 性能更好
- 调试更方便

### 毕设演示

**推荐：MCP 模式**
```bash
start_mcp.bat
```
- 满足毕设要求
- 展示 MCP 架构
- 体现技术深度

---

## 📚 相关文档

- [启动模式说明](./STARTUP_MODE.md)
- [MCP 服务文档](./mcp_server/README.md)
- [实现总结](./MCP_IMPLEMENTATION.md)

---

**最后更新：** 2026-03-26
