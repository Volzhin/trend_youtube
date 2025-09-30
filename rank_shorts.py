from db import get_conn, last_two_stats

def compute_trend_score(video_id: str) -> float:
    rows = last_two_stats(video_id)
    if not rows:
        return 0.0
    if len(rows) == 1:
        # только сегодняшнее значение: скорость = views_today - 0
        speed = rows[0]["view_count"]
        return 0.3 * speed
    # rows[0] -> today, rows[1] -> prev
    today_v = rows[0]["view_count"]
    prev_v = rows[1]["view_count"]
    speed = max(0, today_v - prev_v)

    # для ускорения нужны ещё −1 среза; если нет — принимаем 0
    # можно доработать: брать rolling из 3 дней
    acceleration = 0
    # (расширим позже, когда накопится история)

    return 0.7 * acceleration + 0.3 * speed

def rank_top_n(n: int = 10):
    with get_conn() as con:
        # последние увиденные Shorts
        vids = con.execute("""
            SELECT video_id, title, channel_title, duration_sec
            FROM videos
            WHERE is_short=1
            ORDER BY last_seen DESC
            LIMIT 500
        """).fetchall()
    scored = []
    for row in vids:
        score = compute_trend_score(row["video_id"])
        scored.append((score, dict(row)))
    scored.sort(key=lambda x: x[0], reverse=True)
    return [r[1] for r in scored[:n]]

if __name__ == "__main__":
    top = rank_top_n(10)
    for i, v in enumerate(top, 1):
        print(f"{i:02d}. {v['title']} [{v['video_id']}] ({v['duration_sec']}s)")
