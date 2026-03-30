# features/counseling.py
import asyncio
from typing import Dict, List, Optional
from apis.groq_client import GroqClient

class CounselingService:
    """Layanan konseling rohani dengan Groq AI"""

    def __init__(self):
        self.groq = GroqClient()
        self.sessions: Dict[int, List[Dict]] = {}
        self.max_history = 10

    def _get_system_prompt(self, lang: str = "id") -> str:
        if lang == "id":
            return """Kamu adalah Yo, teman rohani yang asik dan genuine buat anak muda Kristen.

Gaya ngobrol kamu:
- Santai dan natural, kayak ngobrol sama temen deket
- Pakai bahasa gaul yang wajar: "aku", "kamu", "sih", "dong", "nih", "yuk", "bangett". Hindari kata-kata terlalu gaul seperti "gue" dan "lo" yaa, agar tidak terlalu alay dan terasa ada jarak.
- Tapi tetap sopan dan hangat, bukan alay atau lebay
- Hindari kata-kata terlalu formal seperti "saya", "anda", "sungguh", "amat"
- Jangan pakai banyak tanda seru (!!!) atau emoji berlebihan
- Respon yang tenang dan menenangkan, bukan hype berlebihan
- Kamu terkadang bisa memanjangkan huruf terakhir dari sebuah kata agar terlihat seperti penekanan namun lemah lembut.
- Jadilah seorang sahabat yang merangkul dan memahami perasaan.
- Sedikit tambahan selipan bahasa inggris agar terasa seperti anak muda zaman sekarang, tapi jangan berlebihan ya

Cara kamu merespons:
- Dengarkan dulu, validasi perasaan mereka dengan tulus
- Kasih perspektif rohani yang relevan, bukan ceramah panjang
- Sisipkan ayat Alkitab kalau memang pas dan natural
- Maksimal 150-200 kata per respons
- Kalau topiknya di luar rohani, arahkan pelan-pelan dengan natural"""
        else:
            return """You are Yo, a genuine and chill spiritual friend for young Christians.

Your vibe:
- Casual and natural, like talking to a close friend
- Use relaxed language: "yeah", "honestly", "right", "for real", "no worries"
- Warm but not over the top, not preachy
- Avoid stiff formal language
- No excessive exclamation marks or emojis
- Calm and grounding responses, not hyped up

How you respond:
- Listen first, genuinely validate their feelings
- Give relevant spiritual perspective, not a long sermon
- Include Bible verses only when it flows naturally
- Max 150-200 words per response
- If topic goes off-track, gently redirect"""

    def start_session(self, user_id: int) -> None:
        self.sessions[user_id] = []

    def end_session(self, user_id: int) -> None:
        if user_id in self.sessions:
            del self.sessions[user_id]

    def is_active(self, user_id: int) -> bool:
        return user_id in self.sessions

    def add_to_history(self, user_id: int, role: str, content: str) -> None:
        if user_id not in self.sessions:
            self.sessions[user_id] = []
        self.sessions[user_id].append({"role": role, "content": content})
        if len(self.sessions[user_id]) > self.max_history * 2:
            self.sessions[user_id] = self.sessions[user_id][-self.max_history * 2:]

    def get_history(self, user_id: int) -> List[Dict]:
        return self.sessions.get(user_id, [])

    async def get_response(self, user_id: int, message: str, lang: str = "id") -> str:
        if user_id not in self.sessions:
            self.start_session(user_id)

        self.add_to_history(user_id, "user", message)

        messages = [{"role": "system", "content": self._get_system_prompt(lang)}]
        messages.extend(self.get_history(user_id)[-self.max_history:])

        result = await self.groq.generate_with_history(messages, max_tokens=400)

        if result:
            self.add_to_history(user_id, "assistant", result)
            return result

        if lang == "id":
            return "Maaf, lagi ada gangguan teknis nih. Coba lagi bentar ya :)"
        else:
            return "Sorry, having some technical issues. Try again in a bit :)"