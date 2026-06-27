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
        app_id = "GridLens.GridLens.1.0"
        ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID(app_id)
    except Exception:
        pass


def _rebuild_exe():
    """Rebuild the exe via PyInstaller and exit."""
    if getattr(sys, "frozen", False):
        print("--build is only available when running from source (python main.py)")
        sys.exit(1)
    base = Path(__file__).resolve().parent
    spec = base / "GridLens.spec"
    if not spec.exists():
        print("Error: GridLens.spec not found. Run from the project root.")
        sys.exit(1)
    print("Building GridLens.exe ...")
    result = subprocess.run(
        [sys.executable, "-m", "PyInstaller", str(spec), "--noconfirm"],
        cwd=str(base),
    )
    if result.returncode == 0:
        print("Build succeeded!  dist/GridLens.exe updated.")
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
    app.setApplicationName("GridLens")

    # Apply app-wide stylesheet
    from ui.theme import STYLESHEET
    app.setStyleSheet(STYLESHEET)

    # App icon (optional — don't crash if missing)
    icon_path = Path(__file__).parent / "assets" / "icon.ico"
    if icon_path.exists():
        app.setWindowIcon(QIcon(str(icon_path)))

    try:
        from core.config import load_config
        cfg = load_config()
        has_claude = cfg.get("active_profile") and cfg.get("active_profile", {}).get("key")
        has_api_key = has_claude or cfg.get("GROQ_API_KEY") or cfg.get("GEMINI_API_KEY")
        
        if not has_api_key:
            from ui.first_run_wizard import FirstRunWizard
            from PyQt6.QtWidgets import QDialog
            wizard = FirstRunWizard()
            if wizard.exec() == QDialog.DialogCode.Accepted and wizard.should_proceed:
                from core.config import save_config
                save_config(
                    claude_profiles=cfg.get("all_profiles", []),
                    active_claude_profile=cfg.get("active_profile_idx", 0),
                    groq_api_key=wizard.groq_key,
                    gemini_api_key=wizard.gemini_key,
                    ollama_base_url=cfg.get("OLLAMA_BASE_URL", "http://localhost:11434"),
                    default_output=cfg.get("DEFAULT_OUTPUT", "csv"),
                    max_resolution=cfg.get("MAX_RESOLUTION", 2000),
                    auto_fallback=cfg.get("AUTO_FALLBACK", True),
                    custom_schema=cfg.get("CUSTOM_SCHEMA", ""),
                    custom_providers=cfg.get("custom_providers", []),
                )

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
                "GridLens — startup error",
                f"The app failed to start:\n\n{exc}\n\n"
                "A full crash log has been written next to the executable."
            )
        except Exception:
            print(crash_text, file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()