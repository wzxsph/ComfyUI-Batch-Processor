# ComfyUI Batch Processor

[![Python Application](https://github.com/wzxsph/ComfyUI-Batch-Processor/actions/workflows/python-app.yml/badge.svg)](https://github.com/wzxsph/ComfyUI-Batch-Processor/actions/workflows/python-app.yml)

[中文版 (Chinese Version)](./README_zh-cn.md)

> [!NOTE]
> This is my first project on GitHub! It was developed with significant assistance from AI. I am still learning and refining the code, so it might not be perfect. Feedback and suggestions are very welcome!

A modern, fast, and feature-rich automation tool for processing image workflows in ComfyUI. 
Built with Python, CustomTkinter, and WebSockets to provide real-time generations without blocking the user interface.

![UI Demo](./demo.gif)

## ✨ Features
* **Modern Interface**: A sleek dark-mode UI built with `CustomTkinter`.
* **Interactive A/B Slider**: Compare Input and Output images seamlessly using a mouse-driven sliding delimiter.
* **Output Gallery**: Navigate through history using "Next/Prev" buttons to review all generated images.
* **Responsive & Flexible**: Optimized layout that eliminates whitespace. Foldable console to maximize image viewing area.
* **Real-time Logging & Progress**: Connects to the ComfyUI WebSocket server (`ws://`) to track node progress exactly as it runs.
* **Non-Blocking Operations**: Multi-threaded architecture ensures the GUI remains fluid during generations.

## 🛠 Prerequisites
* **Python 3.13+** ([Download](https://www.python.org/downloads/))
* **uv Package Manager** ([GitHub](https://github.com/astral-sh/uv)) - Extremely fast Python package installer
  - **Windows**: `powershell -ExecutionPolicy ByPass -c "irm https://astral.sh/uv/install.ps1 | iex"`
  - **Linux/macOS**: `curl -LsSf https://astral.sh/uv/install.sh | sh`
* **Running ComfyUI instance** ([GitHub](https://github.com/comfyanonymous/ComfyUI))

## 🚀 Installation & Usage

1. **Clone the repository**:
    ```bash
    git clone https://github.com/wzxsph/ComfyUI-Batch-Processor.git
    cd ComfyUI-Batch-Processor
    ```

2. **Quick Start - One-Click Launch Scripts**:
    
    **For Windows**:
    ```batch
    双击运行: 一键启动.bat
    ```
    
    **For Linux/macOS**:
    ```bash
    chmod +x run.sh
    ./run.sh
    ```
    
    These scripts will automatically:
    - Check if Python 3 and `uv` are installed
    - Create a virtual environment (if needed)
    - Install all dependencies
    - Launch the application
    
    > **Note**: If `uv` is newly installed, you may need to close and reopen your terminal for the PATH to be updated.

3. **Manual Run (Alternative)**:
    If you prefer to run manually or the scripts don't work:
    ```bash
    uv run main.py
    ```

3. **In the User Interface**:
    * **Language**: Use the language selector in the top-left corner to switch between English and Chinese (中文) at any time.
    * **Server Config**: Enter your running ComfyUI address (default: `127.0.0.1:8188`).
    * **Directories**: Point "Input Folder" to the folder containing your source images, and "Output Folder" to where you want the results.
    * **API JSON File**: Select your exported ComfyUI workflow (`workflow_api.json`). *Note: Make sure to export in **API Format** from ComfyUI.*
    * **Node IDs**: You must specify the ID of the `LoadImage` node and the `SaveImage` node used in your `workflow_api.json`.
    * **Start**: Click "START BATCH"!

## 🌐 Language Support

The application supports **bilingual interface with manual language switching**:
- **English** (English)
- **中文** (Chinese Simplified)

Your language preference is automatically saved and restored when you restart the application.

## 📝 Dependencies

The project uses `uv` for dependency management. All required packages are automatically installed:
- `requests` - HTTP requests to ComfyUI
- `customtkinter` - Modern dark-mode GUI
- `websocket-client` - WebSocket connections for real-time progress
- `pillow` - Image processing and display

## 📁 File Structure

* `main.py` - The entry point of the application.
* `modern_ui.py` - Contains the `CustomTkinter` UI application logic and the multithreading queue system.
* `comfy_api.py` - A modular API wrapper handling both HTTP requests (`/prompt`, `/upload`) and WebSocket connections (for progress/status).
* `pyproject.toml` - Project configuration containing required dependencies (handled automatically by `uv`).
* `workflow_api.json` - Your default ComfyUI exported API workflow.
* `legacy_scripts/` - An archive of older, procedural scripts replaced by the new architecture.
