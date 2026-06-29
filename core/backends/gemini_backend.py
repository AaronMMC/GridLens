"""
Google Gemini backend — uses gemini-2.5-flash with JSON response mode.

Exposes ``run()`` for extraction and ``test_key()`` for settings validation.
"""
import json
from google import genai
from google.genai import types

def test_key(api_key: str) -> tuple[bool, str]:
    if not api_key:
        return False, "Key cannot be empty"
    try:
        client = genai.Client(api_key=api_key)
        # Quick test call
        client.models.generate_content(
            model='gemini-2.5-flash',
            contents='Hi'
        )
        return True, "Valid API key"
    except Exception as e:
        return False, str(e)

def run(image_bytes: bytes, media_type: str, system_prompt: str, user_prompt: str, api_key: str) -> dict:
    client = genai.Client(api_key=api_key)
    
    response = client.models.generate_content(
        model='gemini-2.5-flash',
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
        return json.loads(response.text)
    except json.JSONDecodeError:
        # Fallback if it didn't return pure JSON
        text = response.text.strip()
        if text.startswith("```json"):
            text = text[7:]
        if text.endswith("```"):
            text = text[:-3]
        return json.loads(text.strip())
