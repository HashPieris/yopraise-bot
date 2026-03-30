import json
import random
import asyncio
from typing import Optional
from apis.groq_client import GroqClient

class QuoteService:
    """Layanan quote rohani dengan Groq dan fallback lokal"""
    def __init__(self):
        self.groq = GroqClient()
        self.local_quotes = self._load_local_quotes()

    def _load_local_quotes(self) -> list:
        try:
            with open("data/quotes.json", "r", encoding="utf-8") as f:
                return json.load(f)
        except:
            return []

    def _get_prompt(self, style: str, lang: str = "id") -> str:
        if lang == "id":
            base = """Buat satu quote rohani Kristen untuk anak muda.
Gaya penulisan: santai, natural, menenangkan. Bukan ceramah, bukan lebay.
Pakai bahasa yang relatable buat anak muda zaman sekarang.
Maksimal 2 kalimat. Tulis langsung quotenya saja tanpa judul atau penjelasan."""

            style_notes = {
                "funny": "Tone: ringan dan sedikit humor yang natural, bukan garing.",
                "casual": "Tone: santai banget, kayak ngobrol sama temen.",
                "formal": "Tone: tetap santai tapi sedikit lebih dalam dan reflektif.",
                "experience": "Tone: personal dan genuine, seperti sharing pengalaman nyata.",
                "Jenius": "Tone: sangat cerdas dan insightful, dengan perspektif yang unik.",
                "Puzzle": "Tone: membuat tebakan dan mengakhirinya dengan pesan keren."
            }
            return base + f"\n{style_notes.get(style, '')}"
        else:
            base = """Create one Christian spiritual quote for young people.
Style: casual, natural, calming. Not preachy, not over the top.
Relatable language for today's youth.
Max 2 sentences. Write only the quote, no title or explanation."""

            style_notes = {
                "funny": "Tone: light with natural subtle humor, not cheesy.",
                "casual": "Tone: super chill, like talking to a close friend.",
                "formal": "Tone: still casual but slightly deeper and reflective.",
                "experience": "Tone: personal and genuine, like sharing a real experience.",
                "Genius": "Tone: highly intelligent and insightful, offering a unique perspective.",
                "Puzzle": "Tone: engaging in guesswork and concluding with a compelling message."
            }
            return base + f"\n{style_notes.get(style, '')}"

    async def get_quote(self, style: str = "random", lang: str = "id") -> str:
        if style == "random":
            style = random.choice(["funny", "casual", "formal", "experience"])

        prompt = self._get_prompt(style, lang)
        result = await self.groq.generate_response(prompt, max_tokens=100)
        if result:
            return result

        # Fallback ke lokal
        if self.local_quotes:
            filtered = [q for q in self.local_quotes if q.get("category") == style]
            pool = filtered if filtered else self.local_quotes
            return random.choice(pool).get("text", "")

        if lang == "id":
            return "Tuhan udah tau kamu capek. Istirahat dulu, Dia tetap pegang kendali kok :)"
        else:
            return "God already knows you're tired. Rest a bit, He's still in control :)"
