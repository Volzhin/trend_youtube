import requests
from tenacity import retry, wait_exponential, stop_after_attempt
from config import YOUTUBE_API_KEY, YOUTUBE_SEARCH_URL, YOUTUBE_API_URL, REGION_CODE, SHORTS_MAX_SECONDS, SEARCH_QUERIES, SEARCH_MAX_RESULTS, SEARCH_ORDER
from db import init_db, upsert_video, insert_stats
from utils import iso_duration_to_seconds, today_str
from genre_analyzer import analyze_genre, get_primary_genre, get_genre_confidence
import time
import random

@retry(wait=wait_exponential(multiplier=1, min=2, max=30), stop=stop_after_attempt(5))
def _search_api_call(params):
    r = requests.get(YOUTUBE_SEARCH_URL, params=params, timeout=20)
    r.raise_for_status()
    return r.json()

@retry(wait=wait_exponential(multiplier=1, min=2, max=30), stop=stop_after_attempt(5))
def _videos_api_call(params):
    r = requests.get(YOUTUBE_API_URL, params=params, timeout=20)
    r.raise_for_status()
    return r.json()

def search_trending_sounds():
    """Поиск трендовых звуков по ключевым словам"""
    init_db()
    total_found = 0
    
    for query in SEARCH_QUERIES:
        print(f"[search_trends] Поиск по запросу: '{query}'")
        
        # Поиск видео по запросу
        search_params = {
            "part": "snippet",
            "q": query,
            "type": "video",
            "regionCode": REGION_CODE,
            "maxResults": SEARCH_MAX_RESULTS,
            "order": SEARCH_ORDER,
            "publishedAfter": "2024-01-01T00:00:00Z",  # Только свежие видео
            "key": YOUTUBE_API_KEY,
        }
        
        try:
            search_data = _search_api_call(search_params)
            video_ids = [item["id"]["videoId"] for item in search_data.get("items", [])]
            
            if not video_ids:
                continue
                
            # Получаем детальную информацию о видео
            videos_params = {
                "part": "snippet,contentDetails,statistics",
                "id": ",".join(video_ids),
                "key": YOUTUBE_API_KEY,
            }
            
            videos_data = _videos_api_call(videos_params)
            items = videos_data.get("items", [])
            
            for item in items:
                vid = item["id"]
                dur_sec = iso_duration_to_seconds(item["contentDetails"]["duration"])
                is_short = dur_sec <= SHORTS_MAX_SECONDS
                
                if not is_short:
                    continue
                
                # Анализируем жанр
                title = item["snippet"]["title"]
                description = item["snippet"].get("description", "")
                tags = item["snippet"].get("tags", [])
                
                genre_scores = analyze_genre(title, description, tags)
                primary_genre = get_primary_genre(genre_scores)
                genre_confidence = get_genre_confidence(genre_scores)
                    
                meta = {
                    "video_id": vid,
                    "title": title,
                    "channel_title": item["snippet"]["channelTitle"],
                    "published_at": item["snippet"]["publishedAt"],
                    "duration_sec": dur_sec,
                    "is_short": True,
                    "region": REGION_CODE,
                    "primary_genre": primary_genre,
                    "genre_confidence": genre_confidence,
                }
                upsert_video(meta)
                
                stats = item.get("statistics", {})
                insert_stats(
                    video_id=vid,
                    snapshot_date=today_str(),
                    view_count=int(stats.get("viewCount", 0)),
                    like_count=int(stats.get("likeCount", 0)) if "likeCount" in stats else None,
                    comment_count=int(stats.get("commentCount", 0)) if "commentCount" in stats else None,
                )
                total_found += 1
                
            # Небольшая пауза между запросами
            time.sleep(random.uniform(0.5, 1.5))
            
        except Exception as e:
            print(f"[search_trends] Ошибка при поиске '{query}': {e}")
            continue
    
    print(f"[search_trends] Найдено {total_found} трендовых Shorts по поисковым запросам")
    return total_found

def search_by_custom_query(query, max_results=50):
    """Поиск по пользовательскому запросу"""
    init_db()
    found = 0
    
    print(f"[search_trends] Пользовательский поиск: '{query}'")
    
    search_params = {
        "part": "snippet",
        "q": query,
        "type": "video",
        "regionCode": REGION_CODE,
        "maxResults": max_results,
        "order": SEARCH_ORDER,
        "publishedAfter": "2024-01-01T00:00:00Z",
        "key": YOUTUBE_API_KEY,
    }
    
    try:
        search_data = _search_api_call(search_params)
        video_ids = [item["id"]["videoId"] for item in search_data.get("items", [])]
        
        if not video_ids:
            return 0
            
        videos_params = {
            "part": "snippet,contentDetails,statistics",
            "id": ",".join(video_ids),
            "key": YOUTUBE_API_KEY,
        }
        
        videos_data = _videos_api_call(videos_params)
        items = videos_data.get("items", [])
        
        for item in items:
            vid = item["id"]
            dur_sec = iso_duration_to_seconds(item["contentDetails"]["duration"])
            is_short = dur_sec <= SHORTS_MAX_SECONDS
            
            if not is_short:
                continue
                
            meta = {
                "video_id": vid,
                "title": item["snippet"]["title"],
                "channel_title": item["snippet"]["channelTitle"],
                "published_at": item["snippet"]["publishedAt"],
                "duration_sec": dur_sec,
                "is_short": True,
                "region": REGION_CODE,
            }
            upsert_video(meta)
            
            stats = item.get("statistics", {})
            insert_stats(
                video_id=vid,
                snapshot_date=today_str(),
                view_count=int(stats.get("viewCount", 0)),
                like_count=int(stats.get("likeCount", 0)) if "likeCount" in stats else None,
                comment_count=int(stats.get("commentCount", 0)) if "commentCount" in stats else None,
            )
            found += 1
            
    except Exception as e:
        print(f"[search_trends] Ошибка при пользовательском поиске: {e}")
        return 0
    
    print(f"[search_trends] Найдено {found} Shorts по запросу '{query}'")
    return found

if __name__ == "__main__":
    search_trending_sounds()
