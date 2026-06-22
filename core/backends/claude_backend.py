import anthropic
import base64
import json


class QuotaExhaustedError(Exception):
    pass


def run(image_bytes, media_type, system_prompt, user_prompt, api_key, model) -> dict:
    client = anthropic.Anthropic(api_key=api_key)
    b64 = base64.standard_b64encode(image_bytes).decode()
    try:
        msg = client.messages.create(
            model=model,
            max_tokens=4096,
            system=system_prompt,
            messages=[{"role": "user", "content": [
                {"type": "image", "source": {"type": "base64",
                 "media_type": media_type, "data": b64}},
                {"type": "text", "text": user_prompt},
            ]}],
        )
    except anthropic.RateLimitError as e:
        raise QuotaExhaustedError(str(e)) from e
    except anthropic.AuthenticationError as e:
        raise RuntimeError("Invalid Claude API key in profile. Check Settings.") from e
    except anthropic.NotFoundError as e:
        raise RuntimeError(f"Claude model '{model}' was not found. Check Settings.") from e
    try:
        return json.loads(msg.content[0].text.strip())
    except json.JSONDecodeError as e:
        raise RuntimeError(
            f"Claude returned invalid JSON. Raw response:\n{msg.content[0].text.strip()[:500]}"
        ) from e


def test_key(api_key: str) -> tuple[bool, str]:
    """Lightweight validation used by the Settings 'Test key' button.
    Returns (ok, message)."""
    if not api_key.strip():
        return False, "Enter a key first."
    try:
        client = anthropic.Anthropic(api_key=api_key.strip())
        client.models.list(limit=1)
        return True, "Key is valid."
    except anthropic.AuthenticationError:
        return False, "Invalid API key."
    except Exception as e:
        return False, f"Could not verify key: {e}"