from typing import Optional
from apis.weather_client import WeatherClient
from features.mood_detector import MoodDetector

class WeatherService:
    """Layanan cuaca terintegrasi dengan mood"""
    
    def __init__(self):
        self.weather_client = WeatherClient()
        self.mood_detector = MoodDetector()
    
    async def get_weather_and_message(self, city: str, lang: str = "id") -> Optional[str]:
        """Dapatkan cuaca dan pesan rohani terkait"""
        weather = await self.weather_client.get_weather(city)
        
        if not weather:
            if lang == "id":
                return f"Maaf, kota '{city}' tidak ditemukan. Coba dengan nama kota lain ya :)"
            else:
                return f"Sorry, city '{city}' not found. Try another city name :)"
        
        # Format pesan cuaca
        weather_msg = self.weather_client.format_weather_message(weather, lang)
        
        # Tambahkan pesan rohani berdasarkan kondisi cuaca
        condition = weather["condition"].lower()
        
        if lang == "id":
            spiritual_msg = self._get_spiritual_message(condition, "id")
        else:
            spiritual_msg = self._get_spiritual_message(condition, "en")
        
        return f"{weather_msg}\n\n{spiritual_msg}"
    
    def _get_spiritual_message(self, condition: str, lang: str) -> str:
        """Dapatkan pesan rohani berdasarkan kondisi cuaca"""
        if lang == "id":
            messages = {
                "hujan": "Hujan adalah berkat Tuhan. Seperti air yang menyuburkan tanah, firman Tuhan menyuburkan jiwa kita.",
                "cerah": "Matahari bersinar, mengingatkan kita pada terang Kristus yang menerangi hidup kita.",
                "mendung": "Awan mendung seperti tantangan hidup. Tapi ingat, di balik awan, matahari tetap bersinar.",
                "petir": "Guruh dan kilat mengingatkan kita pada kuasa Tuhan yang dahsyat. Dia lebih besar dari segala badai hidup."
            }
            
            for key, msg in messages.items():
                if key in condition:
                    return msg
            return "Apapun cuacanya, Tuhan tetap baik. Bersyukurlah selalu :D"
        else:
            messages = {
                "rain": "Rain is God's blessing. Like water nourishes the earth, God's word nourishes our soul.",
                "clear": "The sunshine reminds us of Christ's light that illuminates our lives.",
                "cloud": "Clouds are like life's challenges. Remember, behind the clouds, the sun still shines.",
                "thunder": "Thunder and lightning remind us of God's awesome power. He is greater than any storm."
            }
            
            for key, msg in messages.items():
                if key in condition:
                    return msg
            return "Whatever the weather, God is good. Always be grateful :D"