import sys

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
        print(f"Failed to start Modern UI: {e}")

def main():
    """
    Main entry point of the project.
    """
    print("Welcome to ComfyUI Batch Processor Pro!")
    print("Starting the modern UI...")
    example_modern_ui()

if __name__ == "__main__":
    main()
