import requests
import base64
import json

OLLAMA_MODEL = "qwen2.5vl:7b"
OLLAMA_BASE_URL = "http://localhost:11434"

# BUGFIX: the old 600s (10 min) timeout was tighter than the app's own
# hardware-check messaging, which warns CPU-only / low-VRAM machines can
# take "5-15 minutes per image". On weaker hardware than the dev machine,
# a perfectly normal scan could exceed 10 minutes and get killed as a
# timeout. 30 minutes gives slow hardware real room to finish.
REQUEST_TIMEOUT_SECONDS = 1800


class OllamaNotRunningError(Exception):
    pass


def is_ollama_running(base_url: str = OLLAMA_BASE_URL) -> bool:
    try:
        r = requests.get(f"{base_url}/api/tags", timeout=3)
        return r.status_code == 200
    except Exception:
        return False


def check_model_available(base_url: str = OLLAMA_BASE_URL, model: str = OLLAMA_MODEL) -> bool:
    try:
        r = requests.get(f"{base_url}/api/tags", timeout=3)
        if r.status_code != 200:
            return False
        models = r.json().get("models", [])
        return any(m.get("name", "").startswith(model) for m in models)
    except Exception:
        return False


def pull_model(base_url: str = OLLAMA_BASE_URL, model: str = OLLAMA_MODEL) -> None:
    resp = requests.post(f"{base_url}/api/pull", json={"name": model, "stream": False}, timeout=1800)
    resp.raise_for_status()


def run(image_bytes, media_type, system_prompt, user_prompt, base_url,
        timeout: int = REQUEST_TIMEOUT_SECONDS) -> dict:
    b64 = base64.standard_b64encode(image_bytes).decode()
    try:
        resp = requests.post(
            f"{base_url}/api/chat",
            json={
                "model": OLLAMA_MODEL,
                "stream": False,
                "format": "json",
                "messages": [
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt, "images": [b64]},
                ],
            },
            timeout=timeout,
        )
        resp.raise_for_status()
    except requests.exceptions.ConnectionError:
        raise OllamaNotRunningError(
            "Ollama is not running. Start it with: ollama serve"
        )
    except requests.exceptions.Timeout:
        raise RuntimeError(
            f"Ollama didn't respond within {timeout // 60} minutes. On weaker "
            "hardware, very large or high-resolution images can take a long "
            "time on CPU. Try a lower 'Image max resolution' in Settings, or "
            "use Groq/Claude instead."
        )
    except requests.exceptions.HTTPError as e:
        raise RuntimeError(f"Ollama returned an error: {e}") from e
    except Exception as e:
        raise RuntimeError(f"Ollama error: {e}") from e

    try:
        data = resp.json()
    except Exception as e:
        raise RuntimeError(
            f"Ollama returned a response that wasn't valid JSON at all: {e}\n"
            f"Raw: {resp.text[:500]}"
        ) from e

    content = ""
    try:
        content = data.get("message", {}).get("content", "")
    except (AttributeError, TypeError) as e:
        raise RuntimeError(
            f"Unexpected Ollama response format: {e}\nRaw: {str(data)[:500]}"
        ) from e

    try:
        return json.loads(content.strip())
    except json.JSONDecodeError as e:
        raise RuntimeError(
            f"Ollama returned invalid JSON. Raw response:\n{content[:500]}"
        ) from e