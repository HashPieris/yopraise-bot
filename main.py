import logging
import os
import asyncio
from datetime import datetime
from typing import Dict

from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    Application, CommandHandler, MessageHandler, 
    CallbackQueryHandler, filters, ContextTypes
)

from config import BOT_TOKEN, LOG_LEVEL, LOG_FORMAT
from features.song_downloader import SongDownloader
from features.devotional import DevotionalService
from features.quotes import QuoteService
from features.counseling import CounselingService
from features.mood_detector import MoodDetector
from features.weather import WeatherService
from apis.news_client import NewsClient
from apis.rate_limiter import RateLimiter

# Setup logging
logging.basicConfig(format=LOG_FORMAT, level=getattr(logging, LOG_LEVEL))
logger = logging.getLogger(__name__)

# Initialize services
song_downloader = SongDownloader()
devotional_service = DevotionalService()
quote_service = QuoteService()
counseling_service = CounselingService()
mood_detector = MoodDetector()
weather_service = WeatherService()
news_client = NewsClient()
rate_limiter = RateLimiter(max_requests_per_minute=100, max_requests_per_hour=500)

# User data storage
user_languages: Dict[int, str] = {}
user_last_message: Dict[int, str] = {}

# Text templates
TEXTS = {
    'start': {
        'id': """Hai, aku Yo, teman rohani kamu yang siap nemenin setiap saat.

*Aku bisa bantu kamu:*
    *Download Lagu*
    *Renungan Harian*
    *Quote Rohani* 
    *Konseling* 
    *Cuaca* 
    *Berita Rohani*

*Cara pakai:*
    • Ketik judul lagu
    • Ceritakan perasaanmu
        • /renungan
        • /quote
        • /konseling
        • /cuaca 
        • /berita
        • /stopcounsel
        • /bahasa

Ayo ceritakan apa yang kamu rasakan, aku siap dengerin :)""",
        'en': """Hey, I’m Yo, your spiritual buddy who’s down to roll with you anytime.

*I can help you with:*
    *Download Songs* 
    *Daily Devotional*
    *Spiritual Quotes*
    *Counseling*
    *Weather*
    *Christian News*

*How to use:*
    • Type song title
    • Tell me how you feel
        • /devotional
        • /quote
        • /counsel
        • /weather
        • /news 
        • /stopcounsel
        • /language 

Tell me what you're feeling, I'm ready to listen :)"""
    },
    'help': {
        'id': """*Perintah yang tersedia:*
/lagu  
/renungan
/quote 
/konseling 
/stopcounsel 
/cuaca
/berita 
/bahasa 

Atau cukup:
    • Ketik judul lagu
    • Ceritakan perasaanmu

Ada yang bisa aku bantu? :D""",
        'en': """*Available commands:*
/song 
/devotional
/quote 
/counsel
/stopcounsel
/weather
/news
/language

Or just:
    • Type song title
    • Tell me how you feel 

How can I help you? :D"""
    },
    'language_set': {
        'id': "Bahasa diatur ke Indonesia. Sekarang kita ngobrol pakai bahasa Indonesia ya :)\nKetik /help untuk lihat perintah.",
        'en': "It’s in English mode, let’s roll with English :)\nType /help to see commands."
    },
    'download_start': {
        'id': " Mencari lagu di YouTube...",
        'en': " Searching for the song on YouTube..."
    },
    'download_progress': {
        'id': " Mengunduh audio, tunggu sebentar yaa paling 6 menit...",
        'en': " Downloading audio, gimme about 6 minutes, chill for a bit..."
    },
    'download_success': {
        'id': " Ini lagunya, semoga memberkati :D",
        'en': " Here’s the jam, hope it blesses ya :D"
    },
    'download_failed': {
        'id': """ Gagal mengunduh :(

*Kemungkinan penyebab:*
    • Judul lagu tidak ditemukan
    • Koneksi internet bermasalah
    • FFmpeg belum terinstall

*Tips:*
    • Coba dengan judul yang lebih spesifik
    • Pastikan koneksi stabil
    • Install FFmpeg (bantuan: /ffmpeg)

Coba lagi yaa :(""",
        'en': """ Download failed :(

*Possible reasons:*
    • Song title not found
    • Internet connection issue
    • FFmpeg not installed

*Tips:*
    • Try a more specific title
    • Check your connection
    • Install FFmpeg (help: /ffmpeg)

Try again please :("""
    },
    'ffmpeg_help': {
        'id': """*Cara Install FFmpeg (Windows):*
1. Download dari https://www.gyan.dev/ffmpeg/builds/
2. Pilih ffmpeg-release-full.7z
3. Ekstrak ke C:\ffmpeg
4. Tambahkan C:\ffmpeg\bin ke PATH
5. Restart terminal

*Linux/Mac:*
• Ubuntu: sudo apt install ffmpeg
• Mac: brew install ffmpeg

Setelah install, restart bot ya :)""",
        'en': """*How to Install FFmpeg (Windows):*
1. Download from https://www.gyan.dev/ffmpeg/builds/
2. Choose ffmpeg-release-full.7z
3. Extract to C:\ffmpeg
4. Add C:\ffmpeg\bin to PATH
5. Restart terminal

*Linux/Mac:*
• Ubuntu: sudo apt install ffmpeg
• Mac: brew install ffmpeg

After installation, restart the bot :)"""
    },
    'rate_limit': {
        'id': " *Terlalu banyak request!* Tunggu {wait} detik ya.\n\nTuhan ajar kita sabar :D",
        'en': " *Too many requests!* Please wait {wait} seconds.\n\nGod teaches us patience :D"
    }
}

def get_text(key: str, lang: str = 'id', **kwargs) -> str:
    """Dapatkan teks dalam bahasa yang sesuai"""
    text = TEXTS.get(key, {}).get(lang, TEXTS.get(key, {}).get('id', ''))
    if kwargs:
        text = text.format(**kwargs)
    return text

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handler untuk /start"""
    keyboard = [
        [InlineKeyboardButton("🇮🇩 Indonesia", callback_data="lang_id")],
        [InlineKeyboardButton("🇬🇧 English", callback_data="lang_en")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.message.reply_text(get_text('start', 'id'), reply_markup=reply_markup, parse_mode='Markdown')

async def language_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handler untuk pilihan bahasa"""
    query = update.callback_query
    await query.answer()
    lang = query.data.split('_')[1]
    user_languages[update.effective_user.id] = lang
    await query.edit_message_text(get_text('language_set', lang))
    await query.message.reply_text(get_text('help', lang), parse_mode='Markdown')

async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handler untuk /help"""
    user_id = update.effective_user.id
    lang = user_languages.get(user_id, 'id')
    await update.message.reply_text(get_text('help', lang), parse_mode='Markdown')

async def ffmpeg_help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handler untuk /ffmpeg - bantuan install ffmpeg"""
    user_id = update.effective_user.id
    lang = user_languages.get(user_id, 'id')
    await update.message.reply_text(get_text('ffmpeg_help', lang), parse_mode='Markdown')

async def song_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handler untuk /lagu atau /song"""
    user_id = update.effective_user.id
    lang = user_languages.get(user_id, 'id')
    
    # Rate limiting check
    allowed, limit_type = rate_limiter.check_and_add(user_id)
    if not allowed:
        wait_time = rate_limiter.get_wait_time(user_id)
        await update.message.reply_text(get_text('rate_limit', lang, wait=int(wait_time)), parse_mode='Markdown')
        return
    
    if not context.args:
        await update.message.reply_text("Coba: /lagu Goodness of God" if lang == 'id' else "Try: /song Goodness of God")
        return
    
    query = ' '.join(context.args)
    
    msg = await update.message.reply_text(get_text('download_start', lang))
    await msg.edit_text(get_text('download_progress', lang))
    
    filepath, error = await song_downloader.download_audio(query)
    
    if filepath and os.path.exists(filepath):
        with open(filepath, 'rb') as f:
            await update.message.reply_audio(
                audio=f, 
                title=os.path.basename(filepath).replace('.mp3', ''),
                caption=get_text('download_success', lang)
            )
        await msg.delete()
        # Cleanup file
        try:
            os.remove(filepath)
        except:
            pass
    else:
        await msg.edit_text(get_text('download_failed', lang), parse_mode='Markdown')

async def devotional_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handler untuk /renungan atau /devotional"""
    user_id = update.effective_user.id
    lang = user_languages.get(user_id, 'id')
    
    allowed, _ = rate_limiter.check_and_add(user_id)
    if not allowed:
        wait_time = rate_limiter.get_wait_time(user_id)
        await update.message.reply_text(get_text('rate_limit', lang, wait=int(wait_time)), parse_mode='Markdown')
        return
    
    msg = await update.message.reply_text(" Lagi nyiapin renungannya..." if lang == 'id' else " Preparing devotional...")
    
    devotional = await devotional_service.get_devotional(lang=lang)
    await msg.edit_text(devotional)

async def quote_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handler untuk /quote"""
    user_id = update.effective_user.id
    lang = user_languages.get(user_id, 'id')
    
    allowed, _ = rate_limiter.check_and_add(user_id)
    if not allowed:
        wait_time = rate_limiter.get_wait_time(user_id)
        await update.message.reply_text(get_text('rate_limit', lang, wait=int(wait_time)), parse_mode='Markdown')
        return
    
    style = context.args[0] if context.args else 'random'
    valid_styles = ['funny', 'casual', 'formal', 'experience', 'random']
    if style not in valid_styles:
        style = 'random'
    
    quote = await quote_service.get_quote(style, lang)
    await update.message.reply_text(quote)

async def counsel_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handler untuk /konseling atau /counsel"""
    user_id = update.effective_user.id
    lang = user_languages.get(user_id, 'id')
    
    if counseling_service.is_active(user_id):
        await update.message.reply_text(
            "Kamu sedang dalam sesi konseling. Kirim pesanmu atau /stopcounsel untuk mengakhiri." if lang == 'id'
            else "You're already in a counseling session. Send your message or /stopcounsel to end."
        )
        return
    
    counseling_service.start_session(user_id)
    context.user_data['counseling_mode'] = True
    
    if lang == 'id':
        await update.message.reply_text(
            "*Sesi Konseling Dimulai*\n\n"
            "Aku siap dengerinn. Ceritain apa yang lagi kamu rasain atau pikirin yaa.\n\n"
            "Aku akan bantu dari sudut pandang rohani dengan empati dan kasih.\n\n"
            "Ketik /stopcounsel untuk mengakhiri sesi.",
            parse_mode='Markdown'
        )
    else:
        await update.message.reply_text(
            "*Counseling Session Started*\n\n"
            "I'm here to listen. Tell me what you're feeling or thinking.\n\n"
            "I'll help from a spiritual perspective with empathy and love.\n\n"
            "Type /stopcounsel to end the session.",
            parse_mode='Markdown'
        )

async def stop_counsel_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handler untuk /stopcounsel"""
    user_id = update.effective_user.id
    lang = user_languages.get(user_id, 'id')
    
    counseling_service.end_session(user_id)
    context.user_data['counseling_mode'] = False
    
    if lang == 'id':
        await update.message.reply_text(
            "Sesi konseling diakhiri.\n\n"
            "Jika kamu butuh bantuan lagi, aku selalu di sini yaa. Tuhan memberkatii :D"
            "Chat admin di Whatsapp 08583503160 jika kamu butuh bantuan doa yaa. Tim kami akan bawa nama kamu dalam doa. peace"
        )
    else:
        await update.message.reply_text(
            "Counseling session ended.\n\n"
            "If you need help again, I'm always ready. God bless you :D"
            "Hit up the WhatsApp admin at 08583503160 if you ever need some prayer vibes. Our team got your back and will lift your name up. Peace "
        )

async def weather_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handler untuk /cuaca atau /weather"""
    user_id = update.effective_user.id
    lang = user_languages.get(user_id, 'id')
    
    allowed, _ = rate_limiter.check_and_add(user_id)
    if not allowed:
        wait_time = rate_limiter.get_wait_time(user_id)
        await update.message.reply_text(get_text('rate_limit', lang, wait=int(wait_time)), parse_mode='Markdown')
        return
    
    if not context.args:
        await update.message.reply_text(
            "Coba: /cuaca Jakarta" if lang == 'id' else "Try: /weather Jakarta"
        )
        return
    
    city = ' '.join(context.args)
    await update.message.reply_text("Mengecek cuaca..." if lang == 'id' else "Checking weather...")
    
    result = await weather_service.get_weather_and_message(city, lang)
    await update.message.reply_text(result, parse_mode='Markdown')

async def news_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handler untuk /berita atau /news"""
    user_id = update.effective_user.id
    lang = user_languages.get(user_id, 'id')
    
    allowed, _ = rate_limiter.check_and_add(user_id)
    if not allowed:
        wait_time = rate_limiter.get_wait_time(user_id)
        await update.message.reply_text(get_text('rate_limit', lang, wait=int(wait_time)), parse_mode='Markdown')
        return
    
    msg = await update.message.reply_text("Mengambil berita terbaru..." if lang == 'id' else "Fetching latest news...")
    
    articles = await news_client.get_christian_news()
    if articles:
        news_text = news_client.format_news_message(articles, lang)
        await msg.edit_text(news_text, parse_mode='Markdown')
    else:
        await msg.edit_text(
            "Waduh maaf yaa, beritanya belum ada nih. Coba lagi nanti ya" if lang == 'id'
            else "Sorry, news is not available right now. Try again later :)"
        )

async def handle_text(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handler untuk pesan teks biasa"""
    user_id = update.effective_user.id
    user_text = update.message.text
    lang = user_languages.get(user_id, 'id')
    
    # Rate limiting
    allowed, limit_type = rate_limiter.check_and_add(user_id)
    if not allowed:
        wait_time = rate_limiter.get_wait_time(user_id)
        await update.message.reply_text(get_text('rate_limit', lang, wait=int(wait_time)), parse_mode='Markdown')
        return
    
    # Simpan last message
    user_last_message[user_id] = user_text
    
    # Cek mode konseling
    if context.user_data.get('counseling_mode', False):
        await update.message.chat.send_action(action="typing")
        response = await counseling_service.get_response(user_id, user_text, lang)
        await update.message.reply_text(response)
        return
    
    # Deteksi intent
    lower_text = user_text.lower()
    
    # 1. Deteksi cuaca
    if 'cuaca' in lower_text or 'weather' in lower_text:
        # Extract city
        import re
        patterns = [r"cuaca (?:di )?([a-zA-Z\s]+)", r"weather (?:in )?([a-zA-Z\s]+)"]
        city = None
        for pattern in patterns:
            match = re.search(pattern, lower_text)
            if match:
                city = match.group(1).strip()
                break
        
        if city:
            await update.message.reply_text("Mengecek cuaca..." if lang == 'id' else "Checking weather...")
            result = await weather_service.get_weather_and_message(city, lang)
            await update.message.reply_text(result, parse_mode='Markdown')
            return
    
    # 2. Deteksi berita
    if any(word in lower_text for word in ['berita', 'news']):
        msg = await update.message.reply_text("Mengambil berita terbaru..." if lang == 'id' else "Fetching latest news...")
        articles = await news_client.get_christian_news()
        if articles:
            news_text = news_client.format_news_message(articles, lang)
            await msg.edit_text(news_text, parse_mode='Markdown')
        else:
            await msg.edit_text(
                "Maaf, berita belum tersedia saat ini. Coba lagi nanti :)" if lang == 'id'
                else "Sorry, news is not available right now. Try again later :)"
            )
        return
    
    # 3. Deteksi lagu (judul pendek)
    if len(user_text) < 60 and not any(word in lower_text for word in ['sedih', 'galau', 'kecewa', 'senang', 'capek', 'lelah', 'aku', 'saya']):
        msg = await update.message.reply_text(get_text('download_start', lang))
        await msg.edit_text(get_text('download_progress', lang))
        
        filepath, error = await song_downloader.download_audio(user_text)
        
        if filepath and os.path.exists(filepath):
            with open(filepath, 'rb') as f:
                await update.message.reply_audio(
                    audio=f, 
                    title=os.path.basename(filepath).replace('.mp3', ''),
                    caption=get_text('download_success', lang)
                )
            await msg.delete()
            try:
                os.remove(filepath)
            except:
                pass
        else:
            # Jika gagal, coba lagi dengan "lagu rohani" prefix
            if not any(word in user_text.lower() for word in ['rohani', 'kristen', 'gospel', 'worship']):
                new_query = f"lagu rohani {user_text}" if lang == 'id' else f"christian worship song {user_text}"
                filepath, error = await song_downloader.download_audio(new_query)
                
                if filepath and os.path.exists(filepath):
                    with open(filepath, 'rb') as f:
                        await update.message.reply_audio(
                            audio=f, 
                            title=os.path.basename(filepath).replace('.mp3', ''),
                            caption=get_text('download_success', lang)
                        )
                    await msg.delete()
                    try:
                        os.remove(filepath)
                    except:
                        pass
                    return
            
            await msg.edit_text(get_text('download_failed', lang), parse_mode='Markdown')
        return
    
    # 4. Deteksi mood untuk curhat
    mood, confidence = mood_detector.detect_mood(user_text, lang)
    
    if confidence > 0.3 or len(user_text) > 30:
        # Tampilkan respon mood
        mood_response = mood_detector.get_mood_response(mood, lang)
        
        keyboard = [
            [InlineKeyboardButton("Lagu", callback_data=f"rec_song_{mood}"),
             InlineKeyboardButton("Renungan", callback_data=f"rec_devotional_{mood}"),
             InlineKeyboardButton("Quote", callback_data=f"rec_quote_{mood}")]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await update.message.reply_text(mood_response, reply_markup=reply_markup)
        return
    
    # 5. Default - tampilkan help
    await update.message.reply_text(get_text('help', lang), parse_mode='Markdown')

async def recommend_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handler untuk tombol rekomendasi"""
    query = update.callback_query
    await query.answer()
    
    user_id = update.effective_user.id
    lang = user_languages.get(user_id, 'id')
    data = query.data
    parts = data.split('_')
    
    if len(parts) < 3:
        return
    
    rec_type = parts[1]
    mood = parts[2]
    
    if rec_type == 'song':
        await query.edit_message_text("Mencari lagu yang cocok..." if lang == 'id' else "Finding a suitable song...")
        
        search_query = f"lagu rohani kristen untuk orang yang {mood}" if lang == 'id' else f"christian worship song for {mood}"
        filepath, error = await song_downloader.download_audio(search_query)
        
        if filepath and os.path.exists(filepath):
            with open(filepath, 'rb') as f:
                await query.message.reply_audio(
                    audio=f, 
                    title=os.path.basename(filepath).replace('.mp3', ''),
                    caption=get_text('download_success', lang)
                )
            await query.delete_message()
            try:
                os.remove(filepath)
            except:
                pass
        else:
            await query.edit_message_text(get_text('download_failed', lang), parse_mode='Markdown')
    
    elif rec_type == 'devotional':
        await query.edit_message_text("Menyiapkan renungan..." if lang == 'id' else "Preparing devotional...")
        devotional = await devotional_service.get_devotional(mood, lang)
        await query.edit_message_text(devotional)
    
    elif rec_type == 'quote':
        await query.edit_message_text("Menyiapkan quote..." if lang == 'id' else "Preparing quote...")
        quote = await quote_service.get_quote('random', lang)
        await query.edit_message_text(quote)

async def error_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Global error handler"""
    logger.error(f"Update {update} caused error {context.error}")
    
    if update and update.effective_message:
        await update.effective_message.reply_text(
            "Maaf, terjadi kesalahan. Tim kami sudah diberitahu dan akan segera memperbaikinya. Coba lagi nanti yaa :("
        )

def main():
    """Main function to run the bot"""
    print(" Starting YoPraise Bot...")
    print(" Loading services...")
    
    # Create application
    app = Application.builder().token(BOT_TOKEN).build()
    
    # Add handlers
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("help", help_command))
    app.add_handler(CommandHandler("ffmpeg", ffmpeg_help_command))
    app.add_handler(CommandHandler("lagu", song_command))
    app.add_handler(CommandHandler("song", song_command))
    app.add_handler(CommandHandler("renungan", devotional_command))
    app.add_handler(CommandHandler("devotional", devotional_command))
    app.add_handler(CommandHandler("quote", quote_command))
    app.add_handler(CommandHandler("konseling", counsel_command))
    app.add_handler(CommandHandler("counsel", counsel_command))
    app.add_handler(CommandHandler("stopcounsel", stop_counsel_command))
    app.add_handler(CommandHandler("cuaca", weather_command))
    app.add_handler(CommandHandler("weather", weather_command))
    app.add_handler(CommandHandler("berita", news_command))
    app.add_handler(CommandHandler("news", news_command))
    
    # Callback handlers
    app.add_handler(CallbackQueryHandler(language_callback, pattern="^lang_"))
    app.add_handler(CallbackQueryHandler(recommend_callback, pattern="^rec_"))
    
    # Message handler
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_text))
    
    # Error handler
    app.add_error_handler(error_handler)
    
    print("✅ Bot is running! Press Ctrl+C to stop.")
    
    # Run bot
    app.run_polling()

if __name__ == "__main__":
    main()