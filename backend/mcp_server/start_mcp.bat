@echo off
REM MCP Server 启动脚本 - 使用独立虚拟环境

echo ========================================
echo Starting MCP Server (独立环境)
echo ========================================

REM 检查独立虚拟环境是否存在
if not exist mcp_venv (
    echo 虚拟环境不存在，正在创建...
    python setup_env.py
)

REM 使用独立虚拟环境启动
echo.
echo 🚀 启动 MCP Server...
mcp_venv\Scripts\python.exe server.py

pause
