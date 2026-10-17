@echo off
echo ========================================
echo Starting MCP Mode (HTTP API)
echo ========================================

:: 切换到 backend 目录
cd /d "%~dp0"

:: 启动 MCP HTTP Server（后台运行）
echo [1/2] Starting MCP HTTP Server on port 8001...
start /B python mcp_server\http_server.py

:: 等待 3 秒让 MCP Server 完全启动
timeout /t 3 /nobreak >nul

:: 检查 MCP Server 是否启动成功
echo [2/2] Starting Main Application on port 8000...
python -m app.main mcp
