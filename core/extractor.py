from core.backends import claude_backend, groq_backend, ollama_backend
from core.backends.claude_backend import QuotaExhaustedError
from core.backends.ollama_backend import (
    OllamaNotRunningError, is_ollama_running, check_model_available,
    OLLAMA_BASE_URL
)
from core.hardware_check import check_ollama_requirements

SYSTEM_PROMPT = (
    "You are a precise data extraction assistant. Your only job is to read tables "
    "from images of physical spreadsheets and return their contents as structured "
    "JSON. Never invent data, guess ambiguous text, or fill in blanks with "
    'assumptions. For cells that are genuinely unreadable, use "?".'
)

USER_PROMPT = (
    "Examine the spreadsheet in the image carefully.\n\n"
    "Rules:\n"
    "1. Extract every row and column EXACTLY as written — one-to-one with the physical table.\n"
    "2. Preserve the original column headers from the first row of the table.\n"
    '3. IGNORE any column whose header contains words like "signature", "sign",\n'
    '   "signed", "firma", "initials", or whose cells clearly contain handwritten\n'
    "   cursive signature strokes. Omit these columns entirely from your output.\n"
    "4. For merged or spanned cells, repeat the value in each logical cell it covers.\n"
    '5. For empty cells, use an empty string "".\n'
    '6. For unreadable cells, use "?".\n'
    "7. Return ONLY valid JSON. No markdown fences, no explanation, no preamble.\n\n"
    "JSON format:\n"
    '{\n  "headers": ["Column1", "Column2", ...],\n  "rows": [\n    ["value", "value", ...],\n    ...\n  ]\n}'
)


def get_available_backend(config: dict) -> str:
    profile = config.get("active_profile")
    if profile and profile.get("key"):
        return "claude"
    if config.get("GROQ_API_KEY"):
        return "groq"
    ollama_url = config.get("OLLAMA_BASE_URL", OLLAMA_BASE_URL)
    if is_ollama_running(ollama_url):
        return "ollama"
    return None


def extract_table(image_bytes, media_type, config, status_cb=None,
                   quota_cb=None, ollama_hw_cb=None) -> dict:
    profile = config.get("active_profile")
    groq_key = config.get("GROQ_API_KEY")
    ollama_url = config.get("OLLAMA_BASE_URL", OLLAMA_BASE_URL)
    has_api_key = (profile and profile.get("key")) or groq_key
    has_ollama = is_ollama_running(ollama_url)

    if not has_api_key and not has_ollama:
        raise RuntimeError(
            "No backends available. Open Settings to add an API key "
            "or install Ollama from https://ollama.com"
        )

    # --- Backend 1: active Claude profile ---
    if profile and profile.get("key"):
        try:
            if status_cb:
                status_cb(f"Scanning with Claude ({profile['name']})...")
            return claude_backend.run(
                image_bytes, media_type, SYSTEM_PROMPT, USER_PROMPT,
                profile["key"], profile["model"]
            )
        except QuotaExhaustedError:
            if quota_cb:
                choice = quota_cb(profile, config.get("other_profiles", []))
                if choice == "cancel":
                    raise RuntimeError("Scan cancelled by user.")
                elif choice.startswith("switch:"):
                    idx = int(choice.split(":")[1])
                    alt = config["other_profiles"][idx]
                    if status_cb:
                        status_cb(f"Retrying with {alt['name']}...")
                    return claude_backend.run(
                        image_bytes, media_type, SYSTEM_PROMPT, USER_PROMPT,
                        alt["key"], alt["model"]
                    )
                # choice == "next" -> fall through to Groq

    # --- Backend 2: Groq ---
    if groq_key:
        try:
            if status_cb:
                status_cb("Falling back to Groq (free tier)...")
            return groq_backend.run(
                image_bytes, media_type, SYSTEM_PROMPT, USER_PROMPT,
                groq_key
            )
        except QuotaExhaustedError:
            pass

    # --- Backend 3: Ollama (local) ---
    if not has_ollama:
        raise RuntimeError(
            "Ollama is not running, and no working Claude or Groq key is "
            "configured. Install Ollama from https://ollama.com and run "
            "'ollama serve', or add an API key in Settings."
        )

    # BUGFIX: previously this hardware check + confirmation dialog was placed
    # after an early `return` inside the `if has_ollama:` branch above, which
    # meant it could only ever run when Ollama was NOT already running —
    # i.e. essentially never, since the code immediately above already
    # bails out with an error in that case. The warning never showed for the
    # normal case (Ollama already running), so users on weak/CPU-only
    # hardware got no heads-up before a multi-minute scan. It now always
    # runs right before Ollama is used.
    hw = check_ollama_requirements()
    if ollama_hw_cb and not ollama_hw_cb(hw):
        raise RuntimeError("Scan cancelled — Ollama hardware check declined.")

    if not check_model_available(ollama_url):
        raise RuntimeError(
            "Ollama is running but the model isn't downloaded yet. "
            f"Open Settings → Ollama and click 'Download model', or run: "
            f"ollama pull {ollama_backend.OLLAMA_MODEL}"
        )

    if status_cb:
        status_cb("Scanning with local Ollama (this can take several minutes)...")
    try:
        return ollama_backend.run(
            image_bytes, media_type, SYSTEM_PROMPT, USER_PROMPT,
            ollama_url
        )
    except OllamaNotRunningError as e:
        raise RuntimeError(str(e)) from e