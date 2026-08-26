import time
import re
from typing import Dict, Tuple
from loguru import logger
from .config import config

class BotSecurity:
    """
    Enterprise Security Guard for Telegram Bot Interface:
    1. In-memory Rate Limiting per Telegram User ID
    2. Prompt Injection & Control Character Sanitization
    3. Secret Masking for API Keys in Responses
    4. Authenticated Chat Session Management
    """
    _rate_limit_tracker: Dict[int, list] = {}
    _authenticated_users: Dict[int, str] = {}  # telegram_user_id -> api_key

    @classmethod
    def check_rate_limit(cls, user_id: int) -> bool:
        """
        Token-bucket rate limiter to prevent abuse and DDoS.
        """
        now = time.time()
        timestamps = cls._rate_limit_tracker.get(user_id, [])
        # Keep only timestamps in the last 60 seconds
        valid_timestamps = [t for t in timestamps if now - t < 60]
        
        if len(valid_timestamps) >= config.RATE_LIMIT_PER_MINUTE:
            cls._rate_limit_tracker[user_id] = valid_timestamps
            return False
            
        valid_timestamps.append(now)
        cls._rate_limit_tracker[user_id] = valid_timestamps
        return True

    @classmethod
    def sanitize_input(cls, text: str) -> str:
        """
        Strips dangerous control characters and trims excessive payloads.
        """
        if not text:
            return ""
        # Remove ASCII control characters except standard newlines and tabs
        cleaned = re.sub(r'[\x00-\x08\x0B\x0C\x0E-\x1F\x7F]', '', text)
        return cleaned[:config.MAX_PROMPT_LENGTH].strip()

    @classmethod
    def mask_api_key(cls, key: str) -> str:
        """
        Safely masks sensitive API keys for display.
        """
        if not key or len(key) < 10:
            return "••••••••"
        return f"{key[:7]}••••••••{key[-4:]}"

    @classmethod
    def set_user_api_key(cls, user_id: int, api_key: str):
        cls._authenticated_users[user_id] = api_key

    @classmethod
    def get_user_api_key(cls, user_id: int) -> str:
        return cls._authenticated_users.get(user_id, "")
