#!/bin/bash

echo "============================================"
echo "  ComfyUI 批处理专业版 - 一键启动 (Linux/macOS)"
echo "============================================"
echo ""

# 检查 Python 是否已安装
if ! command -v python3 &> /dev/null; then
    echo "[错误] 未检测到 Python 3！"
    echo "请先安装 Python 3.10 或更高版本"
    echo ""
    echo "Ubuntu/Debian: sudo apt-get install python3 python3-pip python3-venv"
    echo "macOS: brew install python3"
    echo ""
    exit 1
fi

# 检查 uv 是否已安装
if ! command -v uv &> /dev/null; then
    echo "[错误] 未检测到 uv 包管理器！"
    echo "请先安装 uv: https://github.com/astral-sh/uv"
    echo ""
    echo "安装命令 (Linux/macOS):"
    echo "  curl -LsSf https://astral.sh/uv/install.sh | sh"
    echo ""
    echo "安装后需要在当前终端运行: source \$HOME/.cargo/env"
    echo "或重新打开终端窗口"
    echo ""
    exit 1
fi

echo "[信息] 正在启动应用程序..."
echo "[信息] uv 将自动创建虚拟环境并安装依赖..."
echo ""

# 获取脚本所在目录
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
cd "$SCRIPT_DIR"

# 运行应用
uv run main.py

if [ $? -ne 0 ]; then
    echo ""
    echo "[错误] 应用程序启动失败！请检查上方的错误信息。"
    exit 1
fi
