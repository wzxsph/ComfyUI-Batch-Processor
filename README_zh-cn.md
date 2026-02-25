# ComfyUI 批处理专业版 (ComfyUI Batch Processor)

[English Version](./README.md)

> [!NOTE]
> 这是我在 GitHub 上的第一个项目！本项目主要在 AI 的协助下完成。作为一名初学者，代码可能还比较青涩，也可能存在不完善的地方，非常欢迎大家的指正与建议！

这是一个现代、快速且功能丰富的 ComfyUI 工作流自动化处理工具。
基于 Python、CustomTkinter 和 WebSockets 构建，提供实时的生成反馈，且不会卡死用户界面。

## ✨ 特性
* **现代界面**：使用 `CustomTkinter` 构建的精致深色模式 UI。
* **实时日志与进度**：连接到 ComfyUI WebSocket 服务器 (`ws://`)，实时追踪每一个节点的运行进度，与后端完全同步。
* **非阻塞操作**：采用异步线程和队列架构，确保在长时间生成图片的渲染过程中，GUI 界面依然流畅，不卡顿。
* **即时预览**：图片生成完成后，立即在应用程序中原生显示预览图。
* **极简配置**：通过 `uv` 配合 `pyproject.toml` 实现一键依赖管理，无需手动配置复杂的 Python 环境。

## 🛠 前置需求
* [Python 3.13+](https://www.python.org/downloads/)
* [uv](https://github.com/astral-sh/uv) (极速 Python 包管理器)
* 正在运行的 [ComfyUI](https://github.com/comfyanonymous/ComfyUI) 实例

## 🚀 安装与运行

1. **进入项目目录**:
    ```bash
    cd comfyui
    ```

2. **使用 `uv` 启动程序**:
    由于项目包含 `pyproject.toml`，`uv` 会自动创建并使用隔离的虚拟环境 (`.venv`)，安装缺失的依赖（`requests`, `customtkinter`, `websocket-client`, `pillow`），并在几毫秒内启动应用。
    ```bash
    uv run main.py
    ```

3. **在界面中操作**:
    * **服务器配置 (Server Config)**：输入运行中的 ComfyUI 地址（默认：`127.0.0.1:8188`）。
    * **路径设置 (Directories)**："Input Folder" 指向源图片文件夹，"Output Folder" 指向保存结果的文件夹。
    * **API JSON 文件**: 选择你导出的 ComfyUI 工作流 (`workflow_api.json`)。*注意：请确保是从 ComfyUI 中以 **API Format** 格式导出的。*
    * **节点 ID (Node IDs)**: 你需要指定在你的 `workflow_api.json` 中使用的 `LoadImage` 节点和 `SaveImage` 节点的数字 ID。
    * **开始**: 点击 "START BATCH"!

## 📁 文件结构

* `main.py` - 应用程序入口。
* `modern_ui.py` - 包含 `CustomTkinter` UI 逻辑以及多线程队列系统。
* `comfy_api.py` - 模块化的 API 封装，处理 HTTP 请求（/prompt, /upload）和 WebSocket 连接（用于进度/状态追踪）。
* `pyproject.toml` - 项目配置文件，包含所需依赖（由 `uv` 自动处理）。
* `workflow_api.json` - 默认的 ComfyUI 导出 API 工作流。
* `legacy_scripts/` - 存档文件夹，包含被新版本架构替换掉的旧版脚本。
