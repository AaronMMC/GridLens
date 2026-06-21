import sys
import os
from pathlib import Path
from dotenv import load_dotenv

try:
    from ui.main_window import MainWindow
    from PyQt6.QtWidgets import QApplication
    from PyQt6.QtGui import QIcon
except ImportError as e:
    print(f"Missing dependencies: {e}")
    print("Run: pip install anthropic groq openpyxl PyQt6 python-dotenv pyinstaller Pillow GPUtil psutil pdf2image google-api-python-client google-auth-httplib2 google-auth-oauthlib")
    sys.exit(1)


def main():
    env_path = Path(__file__).parent / ".env"
    example_path = Path(__file__).parent / ".env.example"
    if env_path.exists():
        load_dotenv(env_path)
    elif example_path.exists():
        load_dotenv(example_path)

    app = QApplication(sys.argv)
    app.setApplicationName("SpreadsheetScanner")

    icon_path = Path(__file__).parent / "assets" / "icon.ico"
    if icon_path.exists():
        app.setWindowIcon(QIcon(str(icon_path)))

    window = MainWindow()
    window.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()