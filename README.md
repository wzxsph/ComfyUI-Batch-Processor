# ComfyUI Batch Processor

A modern, fast, and feature-rich automation tool for processing image workflows in ComfyUI. 
Built with Python, CustomTkinter, and WebSockets to provide real-time generations without blocking the user interface.

## ✨ Features
* **Modern Interface**: A sleek dark-mode UI built with `CustomTkinter`.
* **Real-time Logging & Progress**: Connects to the ComfyUI WebSocket server (`ws://`) to track node progress exactly as it runs.
* **Non-Blocking Operations**: Uses an asynchronous thread and queue architecture ensuring the GUI remains perfectly fluid during long generations.
* **Instant Preview**: Displays generated images natively in the app immediately after the workflow completes.
* **Easy Setup**: Project dependencies are fully configured via `pyproject.toml` using `uv`.

## 🛠 Prerequisites
* [Python 3.13+](https://www.python.org/downloads/)
* [uv](https://github.com/astral-sh/uv) (Extremely fast Python package installer and resolver)
* A running instance of [ComfyUI](https://github.com/comfyanonymous/ComfyUI)

## 🚀 Installation & Usage

1. **Clone or Navigate** to your directory:
    ```bash
    cd comfyui
    ```

2. **Run the Application using `uv`**:
    Because this project contains a `pyproject.toml`, `uv` will automatically create and use an isolated virtual environment (`.venv`), install missing dependencies (`requests`, `customtkinter`, `websocket-client`, `pillow`), and launch the app in a matter of milliseconds.
    ```bash
    uv run main.py
    ```

3. **In the User Interface**:
    * **Server Config**: Enter your running ComfyUI address (default: `127.0.0.1:8188`).
    * **Directories**: Point "Input Folder" to the folder containing your source images, and "Output Folder" to where you want the results.
    * **API JSON File**: Select your exported ComfyUI workflow (`workflow_api.json`). *Note: Make sure to export in **API Format** from ComfyUI.*
    * **Node IDs**: You must specify the ID of the `LoadImage` node and the `SaveImage` node used in your `workflow_api.json`.
    * **Start**: Click "START BATCH"!

## 📁 File Structure

* `main.py` - The entry point of the application.
* `modern_ui.py` - Contains the `CustomTkinter` UI application logic and the multithreading queue system.
* `comfy_api.py` - A modular API wrapper handling both HTTP requests (`/prompt`, `/upload`) and WebSocket connections (for progress/status).
* `pyproject.toml` - Project configuration containing required dependencies (handled automatically by `uv`).
* `workflow_api.json` - Your default ComfyUI exported API workflow.
* `legacy_scripts/` - An archive of older, procedural scripts replaced by the new architecture.
