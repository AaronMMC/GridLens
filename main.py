import sys
import os
import subprocess
from pathlib import Path

# Guard for PyInstaller windowed mode — stdout/stderr are None when there's
# no console, and some libraries try to write to them on import.
if sys.stdout is None:
    sys.stdout = open(os.devnull, "w")
if sys.stderr is None:
    sys.stderr = open(os.devnull, "w")


def _set_windows_taskbar_icon():
    """Set AppUserModelID so Windows shows our icon in the taskbar."""
    try:
        import ctypes
        app_id = "ScanMe.SpreadsheetScanner.1.0"
        ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID(app_id)
    except Exception:
        pass


def _rebuild_exe():
    """Rebuild the exe via PyInstaller and exit."""
    if getattr(sys, "frozen", False):
        print("--build is only available when running from source (python main.py)")
        sys.exit(1)
    base = Path(__file__).resolve().parent
    spec = base / "SpreadsheetScanner.spec"
    if not spec.exists():
        print("Error: SpreadsheetScanner.spec not found. Run from the project root.")
        sys.exit(1)
    print("Building SpreadsheetScanner.exe ...")
    result = subprocess.run(
        [sys.executable, "-m", "PyInstaller", str(spec), "--noconfirm"],
        cwd=str(base),
    )
    if result.returncode == 0:
        print("Build succeeded!  dist/SpreadsheetScanner.exe updated.")
    else:
        print("Build failed!")
    sys.exit(result.returncode)


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
    if "--build" in sys.argv or "--rebuild" in sys.argv:
        _rebuild_exe()

    _set_windows_taskbar_icon()

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
        app.processEvents()
        sys.exit(app.exec())
    except Exception as exc:
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