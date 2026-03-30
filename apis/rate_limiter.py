import time
import threading
from collections import defaultdict
from datetime import datetime, timedelta

class RateLimiter:
    """Rate limiter untuk mencegah terlalu banyak request"""
    
    def __init__(self, max_requests_per_minute=30, max_requests_per_hour=500):
        self.max_per_minute = max_requests_per_minute
        self.max_per_hour = max_requests_per_hour
        self.requests = defaultdict(list)
        self.lock = threading.Lock()
    
    def _clean_old_requests(self, user_id):
        """Bersihkan request lama"""
        now = datetime.now()
        minute_ago = now - timedelta(minutes=1)
        hour_ago = now - timedelta(hours=1)
        
        if user_id in self.requests:
            # Hapus request lebih dari 1 menit
            self.requests[user_id] = [
                req_time for req_time in self.requests[user_id]
                if req_time > minute_ago
            ]
            
            # Cek juga per jam
            hour_requests = [
                req_time for req_time in self.requests[user_id]
                if req_time > hour_ago
            ]
            
            if len(hour_requests) >= self.max_per_hour:
                return False, "hour"
        
        return True, None
    
    def check_and_add(self, user_id):
        """Cek apakah request diizinkan, jika ya tambahkan ke log"""
        with self.lock:
            allowed, limit_type = self._clean_old_requests(user_id)
            
            if not allowed:
                return False, f"rate_limit_{limit_type}"
            
            if len(self.requests[user_id]) >= self.max_per_minute:
                return False, "rate_limit_minute"
            
            self.requests[user_id].append(datetime.now())
            return True, None
    
    def get_wait_time(self, user_id):
        """Dapatkan waktu tunggu yang disarankan"""
        if user_id not in self.requests:
            return 0
        
        now = datetime.now()
        minute_ago = now - timedelta(minutes=1)
        recent_requests = [
            req_time for req_time in self.requests[user_id]
            if req_time > minute_ago
        ]
        
        if len(recent_requests) >= self.max_per_minute:
            oldest = min(recent_requests)
            wait = 60 - (now - oldest).total_seconds()
            return max(0, wait)
        
        return 0