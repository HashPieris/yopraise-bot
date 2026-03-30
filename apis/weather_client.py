import aiohttp
import asyncio
from typing import Optional, Dict
from cachetools import TTLCache, cached

from config import WEATHER_API_KEY

class WeatherClient:
    """Weather API Client untuk mendapatkan informasi cuaca"""
    
    def __init__(self):
        self.api_key = WEATHER_API_KEY
        self.base_url = "http://api.openweathermap.org/data/2.5"
        self.cache = TTLCache(maxsize=100, ttl=1800)  # 30 menit
    
    @cached(cache=TTLCache(maxsize=100, ttl=1800))
    async def get_weather(self, city: str) -> Optional[Dict]:
        """Dapatkan informasi cuaca untuk kota tertentu"""
        url = f"{self.base_url}/weather"
        params = {
            "q": city,
            "appid": self.api_key,
            "units": "metric",
            "lang": "id"
        }
        
        for attempt in range(3):
            try:
                async with aiohttp.ClientSession() as session:
                    async with session.get(url, params=params, timeout=10) as response:
                        if response.status == 200:
                            data = await response.json()
                            return {
                                "city": data.get("name", city),
                                "temp": data["main"]["temp"],
                                "feels_like": data["main"]["feels_like"],
                                "condition": data["weather"][0]["description"],
                                "humidity": data["main"]["humidity"],
                                "icon": data["weather"][0]["icon"]
                            }
                        elif response.status == 404:
                            return None
                        else:
                            await asyncio.sleep(2 ** attempt)
            except asyncio.TimeoutError:
                print(f"Weather API timeout for {city}, attempt {attempt + 1}")
                await asyncio.sleep(2 ** attempt)
            except Exception as e:
                print(f"Weather API error: {e}")
                await asyncio.sleep(1)
        
        return None
    
    def format_weather_message(self, weather: Dict, lang: str = "id") -> str:
        """Format pesan cuaca untuk ditampilkan ke user"""
        if lang == "id":
            return f"""🌤️ *Cuaca di {weather['city']}*

Suhu: {weather['temp']}°C (terasa {weather['feels_like']}°C)
Kondisi: {weather['condition']}
Kelembaban: {weather['humidity']}%

Jangan lupa jaga kesehatan, Tuhan memberkati :D"""
        else:
            return f"""🌤️ *Weather in {weather['city']}*

Temperature: {weather['temp']}°C (feels like {weather['feels_like']}°C)
Condition: {weather['condition']}
Humidity: {weather['humidity']}%

Don't forget to take care of your health, God bless you :D"""