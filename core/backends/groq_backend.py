import groq
import base64
import json
from core.backends.claude_backend import QuotaExhaustedError

# BUGFIX: this was "qwen-2.5-vl-72b", which is not a Groq-hosted model —
# that name belongs to the local Ollama backend. Groq's actual current
# vision-capable model is Llama 4 Scout. Using the wrong id meant every
# Groq request failed outright (model not found), regardless of whether
# the API key was valid or saved correctly.
GROQ_VISION_MODEL = "meta-llama/llama-4-scout-17b-16e-instruct"


def run(image_bytes, media_type, system_prompt, user_prompt, api_key) -> dict:
    client = groq.Groq(api_key=api_key)
    b64 = base64.standard_b64encode(image_bytes).decode()
    try:
        resp = client.chat.completions.create(
            model=GROQ_VISION_MODEL,
            max_completion_tokens=4096,
            response_format={"type": "json_object"},
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": [
                    {"type": "image_url",
                     "image_url": {"url": f"data:{media_type};base64,{b64}"}},
                    {"type": "text", "text": user_prompt},
                ]},
            ],
        )
    except groq.RateLimitError as e:
        raise QuotaExhaustedError(str(e)) from e
    except groq.AuthenticationError as e:
        raise RuntimeError("Invalid Groq API key. Check Settings.") from e
    except groq.NotFoundError as e:
        raise RuntimeError(
            f"Groq model '{GROQ_VISION_MODEL}' was not found or is unavailable "
            f"for your account. Check console.groq.com/docs/models for the "
            f"current vision model name."
        ) from e
    except Exception as e:
        raise RuntimeError(f"Groq API error: {e}") from e
    try:
        return json.loads(resp.choices[0].message.content.strip())
    except json.JSONDecodeError as e:
        raise RuntimeError(
            f"Groq returned invalid JSON. Raw response:\n{resp.choices[0].message.content.strip()[:500]}"
        ) from e


def test_key(api_key: str) -> tuple[bool, str]:
    """Lightweight validation used by the Settings 'Test key' button.
    Returns (ok, message)."""
    if not api_key.strip():
        return False, "Enter a key first."
    try:
        client = groq.Groq(api_key=api_key.strip())
        client.models.list()
        return True, "Key is valid."
    except groq.AuthenticationError:
        return False, "Invalid API key."
    except Exception as e:
        return False, f"Could not verify key: {e}"