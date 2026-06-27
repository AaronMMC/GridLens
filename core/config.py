"""
Centralised config load / save.  Every module calls into here — no more
path drift between reading and writing.
"""
import json
import os
from dotenv import load_dotenv, set_key

from core.paths import get_env_path, get_env_example_path


def load_config() -> dict:
    env_path = get_env_path()
    if env_path.exists():
        load_dotenv(env_path, override=True)
    else:
        example = get_env_example_path()
        if example.exists():
            load_dotenv(example, override=True)

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

    try:
        custom = json.loads(os.getenv("CUSTOM_PROVIDERS", "[]"))
        if not isinstance(custom, list):
            custom = []
    except json.JSONDecodeError:
        custom = []

    try:
        max_res = int(os.getenv("MAX_RESOLUTION", "2000"))
    except ValueError:
        max_res = 2000

    other = [p for i, p in enumerate(profiles) if i != active]

    return {
        "active_profile":     profiles[active] if 0 <= active < len(profiles) else None,
        "other_profiles":     other,
        "all_profiles":       profiles,
        "active_profile_idx": active,
        "GROQ_API_KEY":       os.getenv("GROQ_API_KEY", "").strip(),
        "GEMINI_API_KEY":     os.getenv("GEMINI_API_KEY", "").strip(),
        "OLLAMA_BASE_URL":    (os.getenv("OLLAMA_BASE_URL", "http://localhost:11434").strip()
                               or "http://localhost:11434"),
        "DEFAULT_OUTPUT":     os.getenv("DEFAULT_OUTPUT", "csv"),
        "MAX_RESOLUTION":     max_res,
        "AUTO_FALLBACK":      os.getenv("AUTO_FALLBACK", "true").lower() == "true",
        "CUSTOM_SCHEMA":      os.getenv("CUSTOM_SCHEMA", ""),
        "custom_providers":   custom,
    }


def _ensure(env_path) -> None:
    if not env_path.exists():
        env_path.parent.mkdir(parents=True, exist_ok=True)
        env_path.touch()


def save_config(
    claude_profiles: list,
    active_claude_profile: int,
    groq_api_key: str,
    gemini_api_key: str,
    ollama_base_url: str,
    default_output: str,
    max_resolution: int,
    auto_fallback: bool,
    custom_schema: str,
    custom_providers: list = None,
) -> None:
    env_path = get_env_path()
    _ensure(env_path)
    s = str(env_path)
    set_key(s, "CLAUDE_PROFILES",       json.dumps(claude_profiles))
    set_key(s, "ACTIVE_CLAUDE_PROFILE", str(active_claude_profile))
    set_key(s, "GROQ_API_KEY",          groq_api_key.strip())
    set_key(s, "GEMINI_API_KEY",        gemini_api_key.strip())
    set_key(s, "OLLAMA_BASE_URL",       ollama_base_url.strip() or "http://localhost:11434")
    set_key(s, "DEFAULT_OUTPUT",        default_output)
    set_key(s, "MAX_RESOLUTION",        str(max_resolution))
    set_key(s, "AUTO_FALLBACK",         str(auto_fallback).lower())
    set_key(s, "CUSTOM_SCHEMA",         custom_schema)
    set_key(s, "CUSTOM_PROVIDERS",      json.dumps(custom_providers or []))
    load_dotenv(s, override=True)


def set_active_profile(idx: int) -> None:
    env_path = get_env_path()
    _ensure(env_path)
    set_key(str(env_path), "ACTIVE_CLAUDE_PROFILE", str(idx))
    load_dotenv(str(env_path), override=True)