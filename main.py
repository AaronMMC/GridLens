import sys
import os
from pathlib import Path

# Guard for PyInstaller windowed mode — stdout/stderr are None when there's
# no console, and some libraries try to write to them on import.
if sys.stdout is None:
    sys.stdout = open(os.devnull, "w")
if sys.stderr is None:
    sys.stderr = open(os.devnull, "w")

try:
    from PyQt6.QtWidgets import QApplication
    from PyQt6.QtGui import QIcon
except ImportError as e:
    print(f"Missing PyQt6: {e}")
    print("Run: pip install PyQt6")
    sys.exit(1)

try:
    from dotenv import load_dotenv
except ImportError as e:
    print(f"Missing python-dotenv: {e}")
    sys.exit(1)


def main():
    # Must import paths AFTER guards above so it can write to stderr/stdout
    from core.paths import get_env_path, get_env_example_path, get_crash_log_path
    env_path = get_env_path()
    if env_path.exists():
        load_dotenv(env_path)
    else:
        example = get_env_example_path()
        if example.exists():
            load_dotenv(example)

    app = QApplication(sys.argv)
    app.setApplicationName("SpreadsheetScanner")

    # Apply app-wide stylesheet
    from ui.theme import STYLESHEET
    app.setStyleSheet(STYLESHEET)

    # App icon (optional — don't crash if missing)
    icon_path = Path(__file__).parent / "assets" / "icon.ico"
    if icon_path.exists():
        app.setWindowIcon(QIcon(str(icon_path)))

    try:
        from ui.main_window import MainWindow
        window = MainWindow()
        window.show()
        sys.exit(app.exec())
    except Exception as exc:
        # Write crash to log file so users can report it; also show a
        # message box so the window doesn't just silently disappear.
        import traceback
        crash_text = traceback.format_exc()
        try:
            log_path = get_crash_log_path()
            with open(log_path, "w", encoding="utf-8") as f:
                f.write(crash_text)
        except Exception:
            pass
        try:
            from PyQt6.QtWidgets import QMessageBox
            QMessageBox.critical(
                None,
                "SpreadsheetScanner — startup error",
                f"The app failed to start:\n\n{exc}\n\n"
                "A full crash log has been written next to the executable."
            )
        except Exception:
            print(crash_text, file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()