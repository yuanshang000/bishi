@echo off
REM MCP Server 启动脚本 (Windows)

echo Starting MCP Server for Student Analytics...

REM 激活虚拟环境（如果有）
if exist ..\venv\Scripts\activate.bat (
    call ..\venv\Scripts\activate.bat
)

REM 安装依赖
echo Installing dependencies...
pip install -r requirements.txt -q

REM 启动服务器
echo MCP Server is starting...
python server.py

pause
