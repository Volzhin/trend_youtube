import os
import sqlite3
from datetime import datetime
from typing import Optional, Dict, Any

from config import DB_PATH

os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)

SCHEMA = """
PRAGMA journal_mode=WAL;

CREATE TABLE IF NOT EXISTS videos (
    video_id TEXT PRIMARY KEY,
    title TEXT,
    channel_title TEXT,
    published_at TEXT,
    duration_sec INTEGER,
    is_short INTEGER DEFAULT 1,
    region TEXT,
    first_seen TEXT,
    last_seen TEXT,
    primary_genre TEXT,
    genre_confidence REAL DEFAULT 0.0
);

CREATE TABLE IF NOT EXISTS stats (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    video_id TEXT,
    snapshot_date TEXT,          -- YYYY-MM-DD
    view_count INTEGER,
    like_count INTEGER,
    comment_count INTEGER,
    FOREIGN KEY(video_id) REFERENCES videos(video_id)
);

CREATE TABLE IF NOT EXISTS downloads (
    video_id TEXT PRIMARY KEY,
    audio_path TEXT,
    downloaded_at TEXT,
    duration_sec INTEGER,
    format TEXT
);
"""

def get_conn():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    with get_conn() as con:
        con.executescript(SCHEMA)

def upsert_video(meta: Dict[str, Any]):
    with get_conn() as con:
        now = datetime.utcnow().isoformat()
        cur = con.cursor()
        cur.execute(
            "SELECT video_id FROM videos WHERE video_id = ?",
            (meta["video_id"],)
        )
        exists = cur.fetchone() is not None
        
        # Извлекаем информацию о жанре
        primary_genre = meta.get("primary_genre")
        genre_confidence = meta.get("genre_confidence", 0.0)
        
        if exists:
            cur.execute("""
                UPDATE videos
                SET title=?, channel_title=?, published_at=?, duration_sec=?,
                    is_short=?, region=?, last_seen=?, primary_genre=?, genre_confidence=?
                WHERE video_id=?""",
                (meta["title"], meta["channel_title"], meta["published_at"],
                 meta["duration_sec"], 1 if meta["is_short"] else 0,
                 meta["region"], now, primary_genre, genre_confidence, meta["video_id"])
            )
        else:
            cur.execute("""
                INSERT INTO videos(video_id, title, channel_title, published_at,
                    duration_sec, is_short, region, first_seen, last_seen, primary_genre, genre_confidence)
                VALUES(?,?,?,?,?,?,?,?,?,?,?)""",
                (meta["video_id"], meta["title"], meta["channel_title"],
                 meta["published_at"], meta["duration_sec"],
                 1 if meta["is_short"] else 0, meta["region"], now, now, primary_genre, genre_confidence)
            )
        con.commit()

def insert_stats(video_id: str, snapshot_date: str, view_count: int,
                 like_count: Optional[int], comment_count: Optional[int]):
    with get_conn() as con:
        con.execute("""
            INSERT INTO stats(video_id, snapshot_date, view_count, like_count, comment_count)
            VALUES(?,?,?,?,?)""", (video_id, snapshot_date, view_count, like_count, comment_count))
        con.commit()

def last_two_stats(video_id: str):
    with get_conn() as con:
        rows = con.execute("""
            SELECT snapshot_date, view_count
            FROM stats
            WHERE video_id=?
            ORDER BY snapshot_date DESC
            LIMIT 2
        """, (video_id,)).fetchall()
        return rows

def not_downloaded_ids(candidates: list[str]) -> list[str]:
    if not candidates:
        return []
    with get_conn() as con:
        qmarks = ",".join(["?"] * len(candidates))
        rows = con.execute(
            f"SELECT video_id FROM downloads WHERE video_id IN ({qmarks})",
            candidates
        ).fetchall()
        already = {r["video_id"] for r in rows}
    return [vid for vid in candidates if vid not in already]

def mark_download(video_id: str, audio_path: str, duration_sec: int, fmt: str = "mp3"):
    with get_conn() as con:
        con.execute("""
            INSERT OR REPLACE INTO downloads(video_id, audio_path, downloaded_at, duration_sec, format)
            VALUES(?,?,?,?,?)
        """, (video_id, audio_path, datetime.utcnow().isoformat(), duration_sec, fmt))
        con.commit()

def get_downloaded_files():
    with get_conn() as con:
        rows = con.execute("""
            SELECT d.video_id, d.audio_path, d.downloaded_at, d.duration_sec,
                   v.title, v.channel_title, v.published_at, v.primary_genre, v.genre_confidence
            FROM downloads d
            JOIN videos v ON d.video_id = v.video_id
            ORDER BY d.downloaded_at DESC
        """).fetchall()
        return [dict(row) for row in rows]

def get_videos_by_genre(genres: list[str], min_confidence: float = 0.1):
    with get_conn() as con:
        if not genres:
            return []
        
        placeholders = ",".join(["?"] * len(genres))
        rows = con.execute(f"""
            SELECT video_id, title, channel_title, published_at, duration_sec,
                   primary_genre, genre_confidence
            FROM videos
            WHERE primary_genre IN ({placeholders}) AND genre_confidence >= ?
            ORDER BY genre_confidence DESC, last_seen DESC
        """, genres + [min_confidence]).fetchall()
        return [dict(row) for row in rows]

def get_genre_statistics():
    with get_conn() as con:
        rows = con.execute("""
            SELECT primary_genre, COUNT(*) as count
            FROM videos
            WHERE primary_genre IS NOT NULL
            GROUP BY primary_genre
            ORDER BY count DESC
        """).fetchall()
        return {row["primary_genre"]: row["count"] for row in rows}
