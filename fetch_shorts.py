import requests
from tenacity import retry, wait_exponential, stop_after_attempt
from config import YOUTUBE_API_KEY, YOUTUBE_API_URL, REGION_CODE, SHORTS_MAX_SECONDS
from db import init_db, upsert_video, insert_stats
from utils import iso_duration_to_seconds, today_str

@retry(wait=wait_exponential(multiplier=1, min=2, max=30), stop=stop_after_attempt(5))
def _api_call(params):
    r = requests.get(YOUTUBE_API_URL, params=params, timeout=20)
    r.raise_for_status()
    return r.json()

def fetch_and_store():
    init_db()
    page_token = None
    total = 0
    while True:
        params = {
            "part": "snippet,contentDetails,statistics",
            "chart": "mostPopular",
            "regionCode": REGION_CODE,
            "maxResults": 50,
            "pageToken": page_token,
            "key": YOUTUBE_API_KEY,
        }
        data = _api_call(params)
        items = data.get("items", [])
        for it in items:
            vid = it["id"]
            dur_sec = iso_duration_to_seconds(it["contentDetails"]["duration"])
            is_short = dur_sec <= SHORTS_MAX_SECONDS
            if not is_short:
                continue
            meta = {
                "video_id": vid,
                "title": it["snippet"]["title"],
                "channel_title": it["snippet"]["channelTitle"],
                "published_at": it["snippet"]["publishedAt"],
                "duration_sec": dur_sec,
                "is_short": True,
                "region": REGION_CODE,
            }
            upsert_video(meta)
            stats = it.get("statistics", {})
            insert_stats(
                video_id=vid,
                snapshot_date=today_str(),
                view_count=int(stats.get("viewCount", 0)),
                like_count=int(stats.get("likeCount", 0)) if "likeCount" in stats else None,
                comment_count=int(stats.get("commentCount", 0)) if "commentCount" in stats else None,
            )
            total += 1

        page_token = data.get("nextPageToken")
        if not page_token:
            break
    print(f"[fetch_shorts] Stored {total} US Shorts snapshots.")

if __name__ == "__main__":
    fetch_and_store()
