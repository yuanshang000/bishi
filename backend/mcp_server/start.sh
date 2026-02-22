#!/bin/bash
# MCP Server 启动脚本 (Linux/Mac)

echo "Starting MCP Server for Student Analytics..."

# 激活虚拟环境（如果有）
if [ -f "../venv/bin/activate" ]; then
    source ../venv/bin/activate
fi

# 安装依赖
echo "Installing dependencies..."
pip install -r requirements.txt -q

# 启动服务器
echo "MCP Server is starting..."
python server.py
