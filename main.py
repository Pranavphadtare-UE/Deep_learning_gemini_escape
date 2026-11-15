
"""Entry point for launching either version of the Escape Room application.

Usage:
    python run.py v2   # Launch the recommended version
    python run.py v1   # Launch the original version
"""

import sys


def main():
    # Use Version 2 when no version is provided.
    selected_version = sys.argv[1].strip().lower() if len(sys.argv) > 1 else "v2"

    # Import the requested application.
    if selected_version == "v1":
        from app_v1 import build as create_app
    elif selected_version == "v2":
        from app_v2 import build as create_app
    else:
        print("Invalid version. Usage: python run.py v1 | v2")
        sys.exit(1)

    # Create and start the Gradio interface.
    application = create_app()
    application.launch()


if __name__ == "__main__":
    main()
