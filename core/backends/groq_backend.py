import groq
import base64
import json
from core.backends.claude_backend import QuotaExhaustedError


def run(image_bytes, media_type, system_prompt, user_prompt, api_key) -> dict:
    client = groq.Groq(api_key=api_key)
    b64 = base64.standard_b64encode(image_bytes).decode()
    try:
        resp = client.chat.completions.create(
            model="qwen-2.5-vl-72b",
            max_tokens=4096,
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
    except Exception as e:
        raise RuntimeError(f"Groq API error: {e}") from e
    try:
        return json.loads(resp.choices[0].message.content.strip())
    except json.JSONDecodeError as e:
        raise RuntimeError(
            f"Groq returned invalid JSON. Raw response:\n{resp.choices[0].message.content.strip()[:500]}"
        ) from e