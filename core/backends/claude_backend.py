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
        raise RuntimeError(f"Invalid Claude API key in profile. Check Settings.") from e
    try:
        return json.loads(msg.content[0].text.strip())
    except json.JSONDecodeError as e:
        raise RuntimeError(
            f"Claude returned invalid JSON. Raw response:\n{msg.content[0].text.strip()[:500]}"
        ) from e