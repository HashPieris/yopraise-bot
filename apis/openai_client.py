import time
import asyncio
from typing import Optional, Dict, Any
from openai import OpenAI, AsyncOpenAI
from tenacity import retry, stop_after_attempt, wait_exponential, retry_if_exception
from cachetools import TTLCache, cached

from config import OPENAI_API_KEY, CACHE_TTL, CACHE_MAX_SIZE
from apis.rate_limiter import RateLimiter

class OpenAIClient:
    """OpenAI Client dengan retry, rate limiting, dan caching"""
    
    def __init__(self):
        self.client = AsyncOpenAI(api_key=OPENAI_API_KEY, timeout=30)
        self.sync_client = OpenAI(api_key=OPENAI_API_KEY, timeout=30)
        self.cache = TTLCache(maxsize=CACHE_MAX_SIZE, ttl=CACHE_TTL)
        self.rate_limiter = RateLimiter(max_requests_per_minute=20)
    
    def _is_retryable_error(self, exception):
        """Cek apakah error bisa di-retry"""
        error_str = str(exception).lower()
        retryable = [
            "rate_limit", "429", "timeout", "connection", "server_error", 
            "500", "502", "503", "504", "overloaded"
        ]
        return any(err in error_str for err in retryable)
    
    @cached(cache=TTLCache(maxsize=500, ttl=3600))
    async def generate_response(self, prompt: str, max_tokens: int = 300, 
                                 temperature: float = 0.7, retry_count: int = 3) -> Optional[str]:
        """Generate response dengan retry mechanism"""
        
        for attempt in range(retry_count):
            try:
                response = await self.client.chat.completions.create(
                    model="gpt-3.5-turbo",
                    messages=[{"role": "user", "content": prompt}],
                    max_tokens=max_tokens,
                    temperature=temperature,
                    timeout=30
                )
                return response.choices[0].message.content.strip()
                
            except Exception as e:
                error_msg = str(e).lower()
                
                if "429" in error_msg or "rate_limit" in error_msg:
                    wait_time = (2 ** attempt) * 2
                    print(f"Rate limit hit, waiting {wait_time}s...")
                    await asyncio.sleep(wait_time)
                    
                elif "timeout" in error_msg:
                    wait_time = 2
                    await asyncio.sleep(wait_time)
                    
                elif attempt == retry_count - 1:
                    print(f"OpenAI error after {retry_count} attempts: {e}")
                    return None
                else:
                    await asyncio.sleep(1)
        
        return None
    
    async def generate_with_history(self, messages: list, max_tokens: int = 400,
                                      temperature: float = 0.7) -> Optional[str]:
        """Generate response dengan history percakapan"""
        
        for attempt in range(3):
            try:
                response = await self.client.chat.completions.create(
                    model="gpt-3.5-turbo",
                    messages=messages,
                    max_tokens=max_tokens,
                    temperature=temperature,
                    timeout=30
                )
                return response.choices[0].message.content.strip()
                
            except Exception as e:
                if "429" in str(e).lower():
                    await asyncio.sleep((2 ** attempt) * 2)
                elif attempt == 2:
                    return None
                else:
                    await asyncio.sleep(1)
        
        return None
    
    def generate_sync(self, prompt: str, max_tokens: int = 300) -> Optional[str]:
        """Synchronous version untuk penggunaan sederhana"""
        try:
            response = self.sync_client.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=[{"role": "user", "content": prompt}],
                max_tokens=max_tokens,
                temperature=0.7,
                timeout=30
            )
            return response.choices[0].message.content.strip()
        except Exception as e:
            print(f"OpenAI sync error: {e}")
            return None