"""
Google Gemini backend — uses gemini-2.5-flash with JSON response mode.

Exposes ``run()`` for extraction and ``test_key()`` for settings validation.
"""
import json
import time
import httpx
from google import genai
from google.genai import types
from google.genai import errors as genai_errors
from core.backends.claude_backend import QuotaExhaustedError

_GEMINI_MODEL = "gemini-2.5-flash"
_REQUEST_TIMEOUT = 60

# Transient, retry-once errors: connection got dropped mid-handshake/response
# rather than a real auth/quota/server problem.
_TRANSIENT_EXCEPTIONS = (
    httpx.RemoteProtocolError,   # "Server disconnected without sending a response"
    httpx.ConnectError,          # includes WinError 10054 resets
    httpx.ReadError,
    httpx.WriteError,
)


def _make_client(api_key: str) -> genai.Client:
    # No verify= override -> httpx uses its default certifi CA bundle,
    # the same trust path Groq's client effectively uses. This is what
    # fixes the WinError 10054 resets seen with verify=True (OS store).
    http_client = httpx.Client(timeout=_REQUEST_TIMEOUT)
    return genai.Client(
        api_key=api_key,
        http_options=types.HttpOptions(
            httpx_client=http_client,
            timeout=_REQUEST_TIMEOUT * 1000,
        ),
    )


def _with_retry(fn, retries: int = 1, delay: float = 1.0):
    """Run fn() and retry once on a transient connection-reset style error."""
    last_exc = None
    for attempt in range(retries + 1):
        try:
            return fn()
        except _TRANSIENT_EXCEPTIONS as e:
            last_exc = e
            if attempt < retries:
                time.sleep(delay)
                continue
            raise
    raise last_exc  # pragma: no cover - unreachable, satisfies linters


def test_key(api_key: str) -> tuple[bool, str]:
    if not api_key.strip():
        return False, "Enter a key first."
    try:
        client = _make_client(api_key.strip())
        _with_retry(lambda: client.models.list())
        return True, "Key is valid."
    except genai_errors.ClientError as e:
        code = e.status.code if e.status else None
        if code in (401, 403):
            return False, "Invalid API key."
        if code == 429:
            return False, "Quota exceeded — try again later."
        return False, f"Gemini error ({code or 'unknown'}): {e}"
    except _TRANSIENT_EXCEPTIONS as e:
        return False, (
            "Connection was reset while contacting Gemini "
            f"({type(e).__name__}). This is usually antivirus/firewall "
            "SSL-inspection or a network/VPN issue, not a bad key. "
            "Try again, or temporarily disable AV web-shield and retest."
        )
    except Exception as e:
        return False, f"Could not verify key: {e}"


def run(image_bytes: bytes, media_type: str, system_prompt: str, user_prompt: str, api_key: str) -> dict:
    client = _make_client(api_key)

    def _call():
        return client.models.generate_content(
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

    try:
        response = _with_retry(_call)
    except genai_errors.ClientError as e:
        code = e.status.code if e.status else 0
        if code == 401 or code == 403:
            raise RuntimeError("Invalid Gemini API key. Check Settings.") from e
        if code == 429:
            raise QuotaExhaustedError("Gemini free-tier quota exhausted.") from e
        raise RuntimeError(f"Gemini API error ({code}): {e}") from e
    except httpx.TimeoutException as e:
        raise RuntimeError(f"Gemini request timed out after {_REQUEST_TIMEOUT}s. Check your network connection.") from e
    except _TRANSIENT_EXCEPTIONS as e:
        raise RuntimeError(
            f"Connection to Gemini was reset ({type(e).__name__}) after retrying. "
            "This is usually antivirus/firewall SSL-inspection or a network/VPN "
            "issue. Try again, or use Claude/Groq/Ollama instead."
        ) from e
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