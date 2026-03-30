import asyncio
import random
from typing import Optional
from apis.groq_client import GroqClient

class DevotionalService:
    def __init__(self):
        self.groq = GroqClient()
        self.local_renungan = self._load_local()

    def _load_local(self) -> list:
        try:
            with open("data/renungan.json", "r", encoding="utf-8") as f:
                return json.load(f)
        except:
            return []

    def _get_prompt(self, mood: Optional[str] = None, lang: str = "id") -> str:
        if lang == "id":
            return f"""Tulis renungan harian Kristen untuk anak muda dengan gaya ngobrol santai.

Bayangkan kamu lagi ngobrol bareng temen di kafe sambil sharing firman Tuhan.
Pakai kata-kata kayak: "aku", "kamu", "sih", "nih", "emang", "btw", "nah", "yuk". hindari "gue" dan "lo" ya agar tidak terlalu alay dan terasa ada jarak.
Contoh pembuka yang natural: "Kamu pernah ngerasa ga..." atau "Jujur nih, aku pernah di titik..."
Sedikit tambahan selipan bahasa inggris agar terasa seperti anak muda zaman sekarang, tapi jangan berlebihan ya. Jadilah seperti seorang sahabat buat anak muda yang lagi ngobrol santai tapi tetap dalam konteks rohani.
Kamu terkadang bisa memanjangkan huruf terakhir dari sebuah kata agar terlihat seperti penekanan namun lemah lembut.

Struktur renungan:
1. Pembuka: cerita/situasi sehari-hari yang relate buat anak muda (2-3 kalimat, pakai bahasa santai)
2. Ayat Alkitab yang relevan (tulis lengkap ayatnya beserta referensinya)
3. Penjelasan: hubungin ayat itu sama kehidupan nyata anak muda sekarang (3-4 kalimat, santai)
4. Aplikasi: satu hal konkret yang bisa dilakuin hari ini (1-2 kalimat)
5. Doa penutup: singkat, personal, kayak lagi ngobrol sama Tuhan (2-3 kalimat)

Panjang total: 200-250 kata.
Tone: hangat, menenangkan, genuine. Bukan khotbah, bukan ceramah.
{f"Mood pembaca: {mood}." if mood else ""}"""
        else:
            return f"""Write a daily Christian devotional for young people in a casual conversational style.

Imagine you're chatting with a friend at a coffee shop while sharing God's word.
Use words like: "honestly", "like", "right", "for real", "btw", "so", "yeah"
Example opener: "Have you ever felt like..." or "Honestly, I've been there too..."

Devotional structure:
1. Opening: a relatable everyday situation for young people (2-3 sentences, casual tone)
2. Bible verse: write it out fully with the reference
3. Explanation: connect the verse to real life for young people today (3-4 sentences, casual)
4. Application: one concrete thing to do today (1-2 sentences)
5. Closing prayer: short, personal, like actually talking to God (2-3 sentences)

Total length: 200-250 words.
Tone: warm, calming, genuine. Not a sermon, not preachy.
{f"Reader's mood: {mood}." if mood else ""}"""

    async def get_devotional(self, mood: Optional[str] = None, lang: str = "id") -> str:
        prompt = self._get_prompt(mood, lang)

        result = await self.groq.generate_response(prompt, max_tokens=600)
        if result:
            return result

        # Fallback ke lokal
        if self.local_renungan:
            return random.choice(self.local_renungan).get("content", "")

        if lang == "id":
            return "Maaff, renungan belum tersedia. Coba lagi nanti yaaa:("
        else:
            return "Sorry, devotional not available. Try again later :("
