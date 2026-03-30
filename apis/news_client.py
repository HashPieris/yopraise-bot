# apis/news_client.py
import aiohttp
import asyncio
from typing import Optional, List, Dict
from config import NEWS_API_KEY

class NewsClient:
    """News API Client untuk mendapatkan berita rohani"""

    def __init__(self):
        self.api_key = NEWS_API_KEY
        self.base_url = "https://newsapi.org/v2"
        self._cache = None  # cache manual
        self._cache_time = 0

    async def get_christian_news(self, category: str = "general") -> Optional[List[Dict]]:
        """Dapatkan berita rohani"""
        import time

        # Gunakan cache jika masih fresh (1 jam)
        if self._cache and (time.time() - self._cache_time) < 3600:
            return self._cache

        url = f"{self.base_url}/everything"
        queries = {
            "general": "Christian OR church OR worship OR faith",
            "inspirational": "Christian inspirational OR faith story",
            "world": "Christian OR church news"
        }
        params = {
            "q": queries.get(category, queries["general"]),
            "apiKey": self.api_key,
            "language": "id",
            "sortBy": "publishedAt",
            "pageSize": 5
        }

        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(url, params=params, timeout=aiohttp.ClientTimeout(total=10)) as response:
                    if response.status == 200:
                        data = await response.json()
                        articles = data.get("articles", [])
                        result = [
                            {
                                "title": a.get("title", ""),
                                "description": a.get("description", ""),
                                "url": a.get("url", ""),
                                "source": a.get("source", {}).get("name", ""),
                                "published": a.get("publishedAt", "")
                            }
                            for a in articles[:5]
                            if a.get("title") and "[Removed]" not in a.get("title", "")
                        ]
                        if result:
                            self._cache = result
                            self._cache_time = time.time()
                            return result
                    else:
                        print(f"News API status: {response.status}")
        except Exception as e:
            print(f"News API error: {e}")

        # Fallback: coba query bahasa Inggris jika bahasa Indonesia kosong
        params["language"] = "en"
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(url, params=params, timeout=aiohttp.ClientTimeout(total=10)) as response:
                    if response.status == 200:
                        data = await response.json()
                        articles = data.get("articles", [])
                        result = [
                            {
                                "title": a.get("title", ""),
                                "description": a.get("description", ""),
                                "url": a.get("url", ""),
                                "source": a.get("source", {}).get("name", ""),
                                "published": a.get("publishedAt", "")
                            }
                            for a in articles[:5]
                            if a.get("title") and "[Removed]" not in a.get("title", "")
                        ]
                        if result:
                            self._cache = result
                            self._cache_time = time.time()
                            return result
        except Exception as e:
            print(f"News API fallback error: {e}")

        return None

    def format_news_message(self, articles: List[Dict], lang: str = "id") -> str:
        """Format berita untuk ditampilkan ke user"""
        if not articles:
            return "Belum ada berita terbaru. Coba lagi nanti :)" if lang == "id" else "No news available. Try again later :)"

        if lang == "id":
            lines = ["*Berita Rohani Terbaru*\n"]
        else:
            lines = ["*Latest Christian News*\n"]

        for i, article in enumerate(articles[:5], 1):
            title = article.get('title', '').strip()
            description = article.get('description', '').strip()
            url = article.get('url', '')
            source = article.get('source', '')

            lines.append(f"{i}. *{title}*")
            if source:
                lines.append(f"   Sumber: {source}" if lang == "id" else f"   Source: {source}")
            if description:
                short_desc = description[:120] + "..." if len(description) > 120 else description
                lines.append(f"   {short_desc}")
            if url:
                lines.append(f"   {url}")
            lines.append("")

        return "\n".join(lines)