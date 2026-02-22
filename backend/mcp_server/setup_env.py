"""
MCP Server 独立虚拟环境安装脚本

由于 MCP 和 FastAPI 有依赖冲突，建议为 MCP Server 创建独立虚拟环境
"""

import subprocess
import sys
import os

def main():
    print("=" * 60)
    print("MCP Server 独立环境配置")
    print("=" * 60)

    # 创建虚拟环境
    venv_dir = "mcp_venv"

    if not os.path.exists(venv_dir):
        print(f"\n📦 创建虚拟环境: {venv_dir}")
        subprocess.run([sys.executable, "-m", "venv", venv_dir])
        print("✅ 虚拟环境创建成功")
    else:
        print(f"\n✅ 虚拟环境已存在: {venv_dir}")

    # 获取虚拟环境的 pip 路径
    if sys.platform == "win32":
        pip_path = os.path.join(venv_dir, "Scripts", "pip.exe")
        python_path = os.path.join(venv_dir, "Scripts", "python.exe")
    else:
        pip_path = os.path.join(venv_dir, "bin", "pip")
        python_path = os.path.join(venv_dir, "bin", "python")

    # 安装依赖
    print("\n📥 安装依赖包...")
    subprocess.run([pip_path, "install", "-r", "requirements.txt", "-q"])
    print("✅ 依赖安装完成")

    print("\n" + "=" * 60)
    print("✅ MCP Server 环境配置完成！")
    print("=" * 60)
    print("\n使用方法:")
    print(f"  Windows: {venv_dir}\\Scripts\\python.exe server.py")
    print(f"  Linux/Mac: {venv_dir}/bin/python server.py")
    print("\n或使用启动脚本:")
    print("  start_mcp.bat (Windows)")
    print("  ./start_mcp.sh (Linux/Mac)")
    print()

if __name__ == "__main__":
    main()
