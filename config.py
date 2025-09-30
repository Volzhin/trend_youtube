import os
from dotenv import load_dotenv

load_dotenv()

YOUTUBE_API_KEY = os.getenv("YOUTUBE_API_KEY", "")
REGION_CODE = os.getenv("REGION_CODE", "US")

SHORTS_MAX_SECONDS = int(os.getenv("SHORTS_MAX_SECONDS", "60"))
TOP_N_DOWNLOAD = int(os.getenv("TOP_N_DOWNLOAD", "10"))

MEDIA_DIR = os.getenv("MEDIA_DIR", "media")
DB_PATH = os.getenv("DB_PATH", "data/shorts.db")

# YouTube Data API
YOUTUBE_API_URL = "https://www.googleapis.com/youtube/v3/videos"
YOUTUBE_SEARCH_URL = "https://www.googleapis.com/youtube/v3/search"

# Поисковые запросы для трендовых звуков
SEARCH_QUERIES = [
    "trending music shorts",
    "viral sound tiktok",
    "popular audio shorts",
    "music trend 2024",
    "catchy beat shorts",
    "viral song snippet",
    "trending audio clip",
    "music short viral",
    "sound trend shorts",
    "popular music clip"
]

# Настройки поиска
SEARCH_MAX_RESULTS = 50
SEARCH_ORDER = "relevance"  # relevance, date, rating, viewCount, title
