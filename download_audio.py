import os
from datetime import datetime
import yt_dlp
from db import mark_download, get_conn, not_downloaded_ids
from config import MEDIA_DIR

def _year_month_dir(base: str) -> str:
    d = datetime.utcnow()
    path = os.path.join(base, f"{d.year}", f"{d.month:02d}")
    os.makedirs(path, exist_ok=True)
    return path

def download_audio_for(video_ids: list[str]) -> None:
    to_download = not_downloaded_ids(video_ids)
    if not to_download:
        print("[download_audio] Nothing to download.")
        return

    out_dir = _year_month_dir(MEDIA_DIR)
    ydl_opts = {
        "format": "bestaudio/best",
        "outtmpl": os.path.join(out_dir, "%(id)s.%(ext)s"),
        "postprocessors": [{
            "key": "FFmpegExtractAudio",
            "preferredcodec": "mp3",
            "preferredquality": "192",
        }],
        "quiet": True,
        "noplaylist": True,
    }

    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        for vid in to_download:
            url = f"https://www.youtube.com/watch?v={vid}"
            try:
                info = ydl.extract_info(url, download=True)
                audio_path = ydl.prepare_filename(info)
                # после постпроцессинга расширение станет .mp3
                audio_path = os.path.splitext(audio_path)[0] + ".mp3"
                duration = int(info.get("duration") or 0)
                mark_download(vid, audio_path, duration, "mp3")
                print(f"[download_audio] OK {vid} -> {audio_path}")
            except Exception as e:
                print(f"[download_audio] FAIL {vid}: {e}")

def latest_trending_top_n_ids(n: int = 10) -> list[str]:
    with get_conn() as con:
        rows = con.execute("""
            SELECT v.video_id
            FROM videos v
            JOIN stats s ON s.video_id = v.video_id
            WHERE v.is_short=1
            GROUP BY v.video_id
            ORDER BY MAX(s.snapshot_date) DESC
            LIMIT ?
        """, (n,)).fetchall()
    return [r["video_id"] for r in rows]

if __name__ == "__main__":
    ids = latest_trending_top_n_ids(10)
    download_audio_for(ids)
