"""
Google Gemini backend — uses gemini-2.5-flash with JSON response mode.

Exposes ``run()`` for extraction and ``test_key()`` for settings validation.

Uses a custom httpx.Client with system SSL verification (verify=True) instead
of certifi's bundled CAs. This mirrors the Groq SDK's approach and ensures
compatibility with corporate proxies / SIP restrictions that inject their own
CA certificates into the OS certificate store.
"""
import json
import httpx
from google import genai
from google.genai import types
from google.genai import errors as genai_errors
from core.backends.claude_backend import QuotaExhaustedError

_GEMINI_MODEL = "gemini-2.5-flash"
_REQUEST_TIMEOUT = 60


def _make_client(api_key: str) -> genai.Client:
    http_client = httpx.Client(verify=True, timeout=_REQUEST_TIMEOUT)
    return genai.Client(
        api_key=api_key,
        http_options=types.HttpOptions(
            httpx_client=http_client,
            timeout=_REQUEST_TIMEOUT * 1000,
        ),
    )


def test_key(api_key: str) -> tuple[bool, str]:
    if not api_key.strip():
        return False, "Enter a key first."
    try:
        client = _make_client(api_key.strip())
        client.models.list()
        return True, "Key is valid."
    except genai_errors.ClientError as e:
        code = e.status.code if e.status else None
        if code in (401, 403):
            return False, "Invalid API key."
        if code == 429:
            return False, "Quota exceeded — try again later."
        return False, f"Gemini error ({code or 'unknown'}): {e}"
    except Exception as e:
        return False, f"Could not verify key: {e}"


def run(image_bytes: bytes, media_type: str, system_prompt: str, user_prompt: str, api_key: str) -> dict:
    client = _make_client(api_key)

    try:
        response = client.models.generate_content(
            model=_GEMINI_MODEL,
            contents=[
                types.Part.from_bytes(data=image_bytes, mime_type=media_type),
                user_prompt
            ],
            config=types.GenerateContentConfig(
                system_instruction=system_prompt,
                response_mime_type="application/json",
                temperature=0.1
            )
        )
    except genai_errors.ClientError as e:
        code = e.status.code if e.status else 0
        if code == 401 or code == 403:
            raise RuntimeError("Invalid Gemini API key. Check Settings.") from e
        if code == 429:
            raise QuotaExhaustedError("Gemini free-tier quota exhausted.") from e
        raise RuntimeError(f"Gemini API error ({code}): {e}") from e
    except httpx.TimeoutException as e:
        raise RuntimeError(f"Gemini request timed out after {_REQUEST_TIMEOUT}s. Check your network connection.") from e
    except httpx.ConnectError as e:
        raise RuntimeError(f"Could not connect to Gemini API. Check your network/firewall settings.") from e
    except Exception as e:
        raise RuntimeError(f"Gemini API error: {e}") from e

    try:
        return json.loads(response.text)
    except json.JSONDecodeError:
        text = response.text.strip()
        if text.startswith("```json"):
            text = text[7:]
        if text.endswith("```"):
            text = text[:-3]
        return json.loads(text.strip())
