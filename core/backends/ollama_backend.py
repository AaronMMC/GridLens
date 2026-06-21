import requests
import base64
import json
OLLAMA_MODEL = "qwen2.5vl:7b"
OLLAMA_BASE_URL = "http://localhost:11434"


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
    resp = requests.post(f"{base_url}/api/pull", json={"name": model, "stream": False}, timeout=600)
    resp.raise_for_status()


def run(image_bytes, media_type, system_prompt, user_prompt, base_url) -> dict:
    b64 = base64.standard_b64encode(image_bytes).decode()
    try:
        resp = requests.post(
            f"{base_url}/api/chat",
            json={
                "model": OLLAMA_MODEL,
                "stream": False,
                "messages": [
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt, "images": [b64]},
                ],
            },
            timeout=600,
        )
        resp.raise_for_status()
    except requests.exceptions.ConnectionError:
        raise OllamaNotRunningError(
            "Ollama is not running. Start it with: ollama serve"
        )
    except requests.exceptions.Timeout:
        raise RuntimeError("Ollama request timed out. The model may still be loading.")
    except Exception as e:
        raise RuntimeError(f"Ollama error: {e}") from e
    try:
        data = resp.json()
        content = data.get("message", {}).get("content", "")
        return json.loads(content.strip())
    except json.JSONDecodeError as e:
        raise RuntimeError(
            f"Ollama returned invalid JSON. Raw response:\n{resp.text[:500]}"
        ) from e
    except (KeyError, TypeError) as e:
        raise RuntimeError(
            f"Unexpected Ollama response format: {e}\nRaw: {resp.text[:500]}"
        ) from e