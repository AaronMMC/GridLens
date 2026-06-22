"""
Single source of truth for reading and writing the app's .env config.

Both ui/main_window.py and ui/settings_dialog.py call into this module
instead of each rolling their own load/save logic. That's what used to
cause the "Groq key doesn't save" bug — two different code paths quietly
drifting out of sync. Now there is exactly one.
"""
import json
import os
from dotenv import load_dotenv, set_key

from core.paths import get_env_path, get_env_example_path

DEFAULT_PROFILES = [{"name": "Personal", "key": "", "model": "claude-sonnet-4-6"}]


def load_config() -> dict:
    env_path = get_env_path()
    if env_path.exists():
        load_dotenv(env_path, override=True)
    else:
        example_path = get_env_example_path()
        if example_path.exists():
            load_dotenv(example_path, override=True)

    try:
        profiles = json.loads(os.getenv("CLAUDE_PROFILES", "[]"))
        if not isinstance(profiles, list):
            profiles = []
    except json.JSONDecodeError:
        profiles = []

    try:
        active = int(os.getenv("ACTIVE_CLAUDE_PROFILE", "0"))
    except ValueError:
        active = 0
    if not profiles:
        active = -1
    elif not (0 <= active < len(profiles)):
        active = 0

    other = [p for i, p in enumerate(profiles) if i != active]

    try:
        max_res = int(os.getenv("MAX_RESOLUTION", "2000"))
    except ValueError:
        max_res = 2000

    return {
        "active_profile": profiles[active] if 0 <= active < len(profiles) else None,
        "other_profiles": other,
        "all_profiles": profiles,
        "active_profile_idx": active,
        "GROQ_API_KEY": os.getenv("GROQ_API_KEY", "").strip(),
        "OLLAMA_BASE_URL": os.getenv("OLLAMA_BASE_URL", "http://localhost:11434").strip()
        or "http://localhost:11434",
        "DEFAULT_OUTPUT": os.getenv("DEFAULT_OUTPUT", "csv"),
        "MAX_RESOLUTION": max_res,
        "AUTO_FALLBACK": os.getenv("AUTO_FALLBACK", "true").lower() == "true",
    }


def _ensure_env_file(env_path) -> None:
    if not env_path.exists():
        env_path.parent.mkdir(parents=True, exist_ok=True)
        env_path.touch()


def save_config(
    claude_profiles: list,
    active_claude_profile: int,
    groq_api_key: str,
    ollama_base_url: str,
    default_output: str,
    max_resolution: int,
    auto_fallback: bool,
) -> None:
    """Persist settings. Raises on failure so the UI can show a real error
    instead of silently pretending it worked."""
    env_path = get_env_path()
    _ensure_env_file(env_path)
    path_str = str(env_path)
    set_key(path_str, "CLAUDE_PROFILES", json.dumps(claude_profiles))
    set_key(path_str, "ACTIVE_CLAUDE_PROFILE", str(active_claude_profile))
    set_key(path_str, "GROQ_API_KEY", groq_api_key.strip())
    set_key(path_str, "OLLAMA_BASE_URL", ollama_base_url.strip() or "http://localhost:11434")
    set_key(path_str, "DEFAULT_OUTPUT", default_output)
    set_key(path_str, "MAX_RESOLUTION", str(max_resolution))
    set_key(path_str, "AUTO_FALLBACK", "true" if auto_fallback else "false")
    # Make sure THIS process sees the change immediately too.
    load_dotenv(path_str, override=True)


def set_active_profile(idx: int) -> None:
    env_path = get_env_path()
    _ensure_env_file(env_path)
    set_key(str(env_path), "ACTIVE_CLAUDE_PROFILE", str(idx))
    load_dotenv(str(env_path), override=True)