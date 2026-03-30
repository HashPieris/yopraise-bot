# apis/gemini_client.py
import asyncio
from typing import Optional
import google.generativeai as genai
from config import GEMINI_API_KEY

class GeminiClient:
    """Google Gemini Client"""

    def __init__(self):
        genai.configure(api_key=GEMINI_API_KEY)
        self.model = genai.GenerativeModel('gemini-2.0-flash-lite')
        self.safety_settings = [
            {"category": "HARM_CATEGORY_HARASSMENT", "threshold": "BLOCK_NONE"},
            {"category": "HARM_CATEGORY_HATE_SPEECH", "threshold": "BLOCK_NONE"},
            {"category": "HARM_CATEGORY_SEXUALLY_EXPLICIT", "threshold": "BLOCK_NONE"},
            {"category": "HARM_CATEGORY_DANGEROUS_CONTENT", "threshold": "BLOCK_NONE"},
        ]

    async def generate_response(self, prompt: str) -> Optional[str]:
        """Generate response dengan 1 retry jika kena rate limit"""
        for attempt in range(2):
            try:
                response = await asyncio.to_thread(
                    self.model.generate_content,
                    prompt,
                    safety_settings=self.safety_settings
                )
                return response.text.strip()
            except Exception as e:
                error_msg = str(e)
                print(f"Gemini error: {e}")

                if "ResourceExhausted" in error_msg or "429" in error_msg:
                    if attempt == 0:
                        print("Rate limit hit, waiting 15s before retry...")
                        await asyncio.sleep(15)
                    else:
                        print("Rate limit persists, giving up.")
                        return None
                elif "404" in error_msg or "NotFound" in error_msg:
                    print("Model not found, check model name.")
                    return None
                else:
                    return None
        return None

    def generate_sync(self, prompt: str) -> Optional[str]:
        try:
            response = self.model.generate_content(
                prompt,
                safety_settings=self.safety_settings
            )
            return response.text.strip()
        except Exception as e:
            print(f"Gemini sync error: {e}")
            return None