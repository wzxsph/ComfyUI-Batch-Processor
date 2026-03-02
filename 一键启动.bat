@echo off
chcp 65001 >nul
title ComfyUI Batch Processor
echo ============================================
echo   ComfyUI 批处理专业版 - 一键启动
echo ============================================
echo.

REM 检查 uv 是否已安装
where uv >nul 2>nul
if %errorlevel% neq 0 (
    echo [错误] 未检测到 uv 包管理器！
    echo 请先安装 uv: https://github.com/astral-sh/uv
    echo 安装命令: powershell -ExecutionPolicy ByPass -c "irm https://astral.sh/uv/install.ps1 | iex"
    pause
    exit /b 1
)

echo [信息] 正在启动应用程序...
echo [信息] uv 将自动创建虚拟环境并安装依赖...
echo.

cd /d "%~dp0"
uv run main.py

if %errorlevel% neq 0 (
    echo.
    echo [错误] 应用程序启动失败！请检查上方的错误信息。
    pause
)
