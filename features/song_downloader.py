import yt_dlp
import os
import subprocess
from typing import Optional, Tuple

from config import DATA_DIR

class SongDownloader:
    def __init__(self):
        self.download_dir = os.path.join(DATA_DIR, "downloads")
        os.makedirs(self.download_dir, exist_ok=True)
    
    def check_ffmpeg(self) -> bool:
        try:
            subprocess.run(['ffmpeg', '-version'], capture_output=True, check=True)
            return True
        except:
            return False
    
    def search_youtube(self, query: str) -> Optional[str]:
        ydl_opts = {'quiet': True, 'extract_flat': True, 'format': 'best', 'no_warnings': True}
        try:
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                info = ydl.extract_info(f"ytsearch:{query}", download=False)
                if info and 'entries' in info and info['entries']:
                    return info['entries'][0]['url']
        except Exception as e:
            print(f"Search error: {e}")
        return None
    
    async def download_audio(self, query: str) -> Tuple[Optional[str], Optional[str]]:
        if not self.check_ffmpeg():
            return None, "ffmpeg_not_installed"
        
        url = self.search_youtube(query)
        if not url:
            return None, "not_found"
        
        safe_title = "".join(c for c in query[:50] if c.isalnum() or c in " _-").strip()
        filepath = os.path.join(self.download_dir, f"{safe_title}.mp3")
        
        if os.path.exists(filepath):
            return filepath, None
        
        ydl_opts = {
            'format': 'bestaudio/best',
            'postprocessors': [{'key': 'FFmpegExtractAudio', 'preferredcodec': 'mp3', 'preferredquality': '128'}],
            'outtmpl': os.path.join(self.download_dir, safe_title),
            'quiet': True,
            'no_warnings': True,
            'extractor_args': {'youtube': {'player_client': ['android', 'web']}}
        }
        
        try:
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                ydl.download([url])
                for f in os.listdir(self.download_dir):
                    if f.startswith(safe_title) and f.endswith('.mp3'):
                        return os.path.join(self.download_dir, f), None
            return None, "download_failed"
        except Exception as e:
            print(f"Download error: {e}")
            return None, "download_error"
