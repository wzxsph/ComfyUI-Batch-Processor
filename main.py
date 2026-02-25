def example_modern_ui():
    """
    Example function to showcase the new Modern CustomTkinter UI.
    Initializes the app and starts the main loop.
    """
    try:
        from modern_ui import ModernComfyUIApp
        app = ModernComfyUIApp()
        app.mainloop()
    except Exception as e:
        with open("crash_log_ui.txt", "w") as f:
            f.write(f"Failed to start Modern UI:\n")
            import traceback
            traceback.print_exc(file=f)

import traceback

def main():
    """
    Main entry point of the project.
    """
    try:
        # Avoid using print statements in windowed mode as sys.stdout can be None and cause crashes
        example_modern_ui()
    except Exception as e:
        with open("crash_log.txt", "w") as f:
            f.write("Application crashed on startup:\n")
            traceback.print_exc(file=f)

if __name__ == "__main__":
    main()
