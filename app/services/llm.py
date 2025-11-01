import os
from typing import Optional
import httpx


GEMINI_API_URL = "https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash:generateContent"


def maybe_generate(prompt: str, system: Optional[str] = None) -> Optional[str]:
    api_key = os.getenv("GOOGLE_API_KEY")
    if not api_key:
        return None
    headers = {"Content-Type": "application/json"}
    params = {"key": api_key}
    contents = []
    if system:
        contents.append({"role": "user", "parts": [{"text": system}]})
    contents.append({"role": "user", "parts": [{"text": prompt}]})
    payload = {"contents": contents}
    try:
        with httpx.Client(timeout=20) as client:
            r = client.post(GEMINI_API_URL, headers=headers, params=params, json=payload)
            r.raise_for_status()
            data = r.json()
            text = data["candidates"][0]["content"]["parts"][0]["text"]
            return text.strip()
    except Exception:
        return None


