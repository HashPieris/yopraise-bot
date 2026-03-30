import re
from typing import Tuple, Dict

class MoodDetector:
    """Deteksi mood dari teks dengan multiple keyword dan scoring"""
    
    def __init__(self):
        self.mood_keywords = {
            "sedih": {
                "id": ["sedih", "kecewa", "patah hati", "galau", "menangis", "sendiri", 
                       "putus asa", "down", "gagal", "kehilangan", "hampa", "kosong"],
                "en": ["sad", "disappointed", "heartbroken", "lonely", "cry", "alone", 
                       "hopeless", "down", "failed", "lost", "empty"],
                "weight": 3
            },
            "senang": {
                "id": ["senang", "suka", "bersyukur", "gembira", "happy", "terharu", 
                       "semangat", "bersukacita", "bahagia", "ceria"],
                "en": ["happy", "glad", "grateful", "joyful", "excited", "blessed", 
                       "thankful", "joy", "cheerful"],
                "weight": 3
            },
            "lelah": {
                "id": ["lelah", "capek", "letih", "jenuh", "bosan", "stress", "lelah", 
                       "lelah", "frustrasi", "burnout"],
                "en": ["tired", "exhausted", "bored", "stress", "overwhelmed", "drained", 
                       "fatigued", "weary"],
                "weight": 2
            },
            "marah": {
                "id": ["marah", "kesal", "benci", "kecewa berat", "geram", "jengkel", 
                       "sebel", "emosi"],
                "en": ["angry", "mad", "hate", "annoyed", "frustrated", "rage", "furious"],
                "weight": 2
            },
            "cemas": {
                "id": ["cemas", "khawatir", "takut", "gelisah", "resah", "waswas", 
                       "cemas", "panik"],
                "en": ["anxious", "worried", "fear", "nervous", "panic", "concerned"],
                "weight": 3
            },
            "butuh motivasi": {
                "id": ["semangat", "motivasi", "kuat", "bantu", "doa", "support", "tolong", 
                       "aku butuh", "mohon", "bimbing", "arah"],
                "en": ["motivation", "strength", "help", "pray", "support", "encourage", 
                       "need", "guide", "direction"],
                "weight": 4
            }
        }
        
        self.mood_responses = {
            "sedih": {
                "id": "Aku dengar kamu lagi sedih. Tuhan tahu perasaanmu. Mau aku kasih lagu yang menenangkan atau renungan yang menguatkan?",
                "en": "I hear you're feeling sad. God knows how you feel. Would you like a comforting song or an encouraging devotional?"
            },
            "senang": {
                "id": "Senang dengar kamu lagi bersukacita! Mari kita rayakan kebaikan Tuhan. Mau lagu pujian atau renungan syukur?",
                "en": "Glad to hear you're joyful! Let's celebrate God's goodness. Would you like a praise song or a gratitude devotional?"
            },
            "lelah": {
                "id": "Kamu pasti capek ya. Istirahat sejenak yuk. Tuhan janji akan memberikan kekuatan baru. Mau lagu yang menenangkan atau renungan untuk yang lelah?",
                "en": "You must be tired. Take a moment to rest. God promises to give new strength. Would you like a calming song or a devotional for the weary?"
            },
            "marah": {
                "id": "Emosi lagi naik ya? Coba tarik napas dulu. Tuhan mengerti. Mau lagu yang menenangkan hati atau renungan tentang mengelola emosi?",
                "en": "Feeling upset? Take a deep breath. God understands. Would you like a calming song or a devotional about managing emotions?"
            },
            "cemas": {
                "id": "Khawatir memang berat. Tapi ingat, Tuhan pegang masa depan kita. Mau lagu tentang pengharapan atau renungan tentang ketenangan?",
                "en": "Worry is heavy. But remember, God holds our future. Would you like a song about hope or a devotional about peace?"
            },
            "butuh motivasi": {
                "id": "Semangat! Tuhan punya rencana indah untukmu. Mau lagu penyemangat atau renungan yang memotivasi?",
                "en": "Keep going! God has a beautiful plan for you. Would you like an uplifting song or a motivational devotional?"
            },
            "netral": {
                "id": "Terima kasih sudah cerita. Ada yang bisa aku bantu hari ini? Bisa lagu, renungan, atau quote rohani :)",
                "en": "Thanks for sharing. Anything I can help with today? Songs, devotionals, or spiritual quotes are available :)"
            }
        }
    
    def detect_mood(self, text: str, lang: str = "id") -> Tuple[str, float]:
        """Deteksi mood dengan scoring system"""
        text_lower = text.lower()
        scores = {}
        
        for mood, data in self.mood_keywords.items():
            keywords = data.get(lang, data.get("id", []))
            weight = data.get("weight", 1)
            score = 0
            
            for keyword in keywords:
                if keyword in text_lower:
                    score += weight
                    # Bonus untuk multiple matches
                    if text_lower.count(keyword) > 1:
                        score += 1
            
            if score > 0:
                scores[mood] = score
        
        if scores:
            # Ambil mood dengan score tertinggi
            detected_mood = max(scores, key=scores.get)
            confidence = scores[detected_mood] / (max(scores.values()) + 1)
            return detected_mood, confidence
        
        return "netral", 0.0
    
    def get_mood_response(self, mood: str, lang: str = "id") -> str:
        """Dapatkan respons berdasarkan mood"""
        mood_data = self.mood_responses.get(mood, self.mood_responses["netral"])
        return mood_data.get(lang, mood_data["id"])
    
    def extract_location(self, text: str) -> str:
        """Ekstrak lokasi dari teks (untuk fitur cuaca)"""
        patterns = [
            r"(?:di|di kota|di daerah) ([a-zA-Z\s]+)",
            r"cuaca (?:di )?([a-zA-Z\s]+)",
            r"weather (?:in )?([a-zA-Z\s]+)"
        ]
        
        for pattern in patterns:
            match = re.search(pattern, text.lower())
            if match:
                city = match.group(1).strip()
                if len(city) > 3 and len(city) < 50:
                    return city
        
        return None