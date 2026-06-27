"""
Centralized path resolution for the app's persistent config (.env).

Why this file exists
---------------------
Previously, three different parts of the app computed the .env path in
three different ways:

  - main.py            ->  Path(__file__).parent / ".env"
  - ui/main_window.py  ->  Path(__file__).parent.parent / ".env"
  - ui/settings_dialog.py -> Path(".env")   (relative to cwd)

That's harmless when running from source with `python main.py`, because
all three happen to land on the project root. But once packaged with
PyInstaller (`--onefile`), `__file__` no longer points next to the .exe —
it points inside a temporary extraction folder that PyInstaller wipes
and recreates on every launch. So:

  - main.py loaded .env from the temp folder (effectively always falling
    back to the bundled .env.example, since a real .env was never there).
  - settings_dialog.py saved to a file relative to the current working
    directory, which is a *different* file than the one main.py read.

Result: you'd type in a Groq key, hit Save, and the app would behave as
if nothing happened — because it was reading from one file and writing
to another. This module fixes that by giving every part of the app one
function to call.
"""
import sys
import os
from pathlib import Path

APP_NAME = "GridLens"


def get_app_dir() -> Path:
    """Folder the app's persistent files should live in.

    - Packaged .exe (PyInstaller): the folder containing the .exe.
    - Running from source (`python main.py`): the project root.
    """
    if getattr(sys, "frozen", False):
        return Path(sys.executable).resolve().parent
    return Path(__file__).resolve().parent.parent


def get_user_data_dir() -> Path:
    """Guaranteed-writable fallback (used only if the app's own folder
    isn't writable, e.g. installed under Program Files without admin)."""
    base = os.getenv("APPDATA") or str(Path.home())
    path = Path(base) / APP_NAME
    path.mkdir(parents=True, exist_ok=True)
    return path


def _is_writable(directory: Path) -> bool:
    try:
        probe = directory / ".write_test"
        probe.touch()
        probe.unlink()
        return True
    except Exception:
        return False


def get_env_path() -> Path:
    """The one canonical .env path. Every module must use this."""
    app_dir = get_app_dir()
    env_path = app_dir / ".env"
    if env_path.exists():
        return env_path
    if _is_writable(app_dir):
        return env_path
    return get_user_data_dir() / ".env"


def get_env_example_path() -> Path:
    return get_app_dir() / ".env.example"


def get_crash_log_path() -> Path:
    app_dir = get_app_dir()
    if _is_writable(app_dir):
        return app_dir / "crash_log.txt"
    return get_user_data_dir() / "crash_log.txt"