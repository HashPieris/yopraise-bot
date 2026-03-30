# apis/groq_client.py
import asyncio
from typing import Optional, List, Dict
from groq import Groq
from config import GROQ_API_KEY

class GroqClient:
    """Groq AI Client - cepat, gratis, tanpa quota harian"""

    def __init__(self):
        self.client = Groq(api_key=GROQ_API_KEY)
        self.model = "llama-3.1-8b-instant"  # cepat dan gratis

    async def generate_response(self, prompt: str, max_tokens: int = 500) -> Optional[str]:
        """Generate response dari prompt sederhana"""
        try:
            response = await asyncio.to_thread(
                self.client.chat.completions.create,
                model=self.model,
                messages=[{"role": "user", "content": prompt}],
                max_tokens=max_tokens,
                temperature=0.7,
            )
            return response.choices[0].message.content.strip()
        except Exception as e:
            print(f"Groq error: {e}")
            return None

    async def generate_with_history(self, messages: List[Dict], max_tokens: int = 500) -> Optional[str]:
        """Generate response dengan history percakapan (untuk konseling)"""
        try:
            response = await asyncio.to_thread(
                self.client.chat.completions.create,
                model=self.model,
                messages=messages,
                max_tokens=max_tokens,
                temperature=0.7,
            )
            return response.choices[0].message.content.strip()
        except Exception as e:
            print(f"Groq history error: {e}")
            return None