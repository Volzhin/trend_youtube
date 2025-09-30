from flask import Flask, render_template, send_file, jsonify, request
import os
from db import get_downloaded_files, init_db, get_videos_by_genre, get_genre_statistics
from pipeline import run_pipeline
from rank_shorts import rank_top_n
from search_trends import search_by_custom_query

app = Flask(__name__)

@app.route('/')
def index():
    files = get_downloaded_files()
    return render_template('index.html', files=files)

@app.route('/api/files')
def api_files():
    files = get_downloaded_files()
    return jsonify(files)

@app.route('/api/trending')
def api_trending():
    from db import get_conn
    with get_conn() as con:
        rows = con.execute("""
            SELECT v.video_id, v.title, v.channel_title, v.duration_sec,
                   v.primary_genre, v.genre_confidence,
                   s.view_count, s.like_count, s.comment_count, s.snapshot_date
            FROM videos v
            LEFT JOIN (
                SELECT video_id, view_count, like_count, comment_count, snapshot_date,
                       ROW_NUMBER() OVER (PARTITION BY video_id ORDER BY snapshot_date DESC) as rn
                FROM stats
            ) s ON v.video_id = s.video_id AND s.rn = 1
            WHERE v.is_short = 1
            ORDER BY v.last_seen DESC
            LIMIT 10
        """).fetchall()
    
    trending = []
    for row in rows:
        item = {
            "video_id": row["video_id"],
            "title": row["title"],
            "channel_title": row["channel_title"],
            "duration_sec": row["duration_sec"],
            "primary_genre": row["primary_genre"],
            "genre_confidence": row["genre_confidence"],
            "stats": {
                "view_count": row["view_count"] or 0,
                "like_count": row["like_count"] or 0,
                "comment_count": row["comment_count"] or 0,
                "last_updated": row["snapshot_date"]
            }
        }
        trending.append(item)
    
    return jsonify(trending)

@app.route('/download/<video_id>')
def download_file(video_id):
    files = get_downloaded_files()
    for file_info in files:
        if file_info['video_id'] == video_id:
            audio_path = file_info['audio_path']
            if os.path.exists(audio_path):
                return send_file(audio_path, as_attachment=True, 
                               download_name=f"{video_id}.mp3")
    return "Файл не найден", 404

@app.route('/run_pipeline', methods=['POST'])
def run_pipeline_endpoint():
    try:
        run_pipeline()
        return jsonify({"status": "success", "message": "Пайплайн выполнен успешно"})
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500

@app.route('/search', methods=['POST'])
def search_custom():
    try:
        data = request.get_json()
        query = data.get('query', '').strip()
        max_results = data.get('max_results', 50)
        
        if not query:
            return jsonify({"status": "error", "message": "Поисковый запрос не может быть пустым"}), 400
        
        found = search_by_custom_query(query, max_results)
        return jsonify({"status": "success", "message": f"Найдено {found} Shorts по запросу '{query}'", "found": found})
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500

@app.route('/api/search_queries')
def api_search_queries():
    from config import SEARCH_QUERIES
    return jsonify(SEARCH_QUERIES)

@app.route('/api/genres')
def api_genres():
    stats = get_genre_statistics()
    return jsonify(stats)

@app.route('/api/videos_by_genre')
def api_videos_by_genre():
    genres = request.args.getlist('genres')
    min_confidence = float(request.args.get('min_confidence', 0.1))
    
    if not genres:
        return jsonify([])
    
    videos = get_videos_by_genre(genres, min_confidence)
    return jsonify(videos)

@app.route('/api/search_and_download')
def api_search_and_download():
    """
    API endpoint для поиска треков и получения ссылок на скачивание
    Пример: GET /api/search_and_download?query=moto%20x3m&max_results=10
    """
    try:
        query = request.args.get('query', '').strip()
        max_results = int(request.args.get('max_results', 10))
        
        if not query:
            return jsonify({
                "status": "error", 
                "message": "Параметр 'query' обязателен"
            }), 400
        
        # Выполняем поиск
        found = search_by_custom_query(query, max_results)
        
        if found == 0:
            return jsonify({
                "status": "success",
                "message": f"По запросу '{query}' ничего не найдено",
                "query": query,
                "found": 0,
                "download_links": []
            })
        
        # Получаем информацию о найденных видео (включая нескачанные)
        from db import get_conn
        with get_conn() as con:
            rows = con.execute("""
                SELECT v.video_id, v.title, v.channel_title, v.duration_sec,
                       v.primary_genre, v.genre_confidence,
                       d.audio_path, d.downloaded_at
                FROM videos v
                LEFT JOIN downloads d ON v.video_id = d.video_id
                WHERE v.is_short = 1 AND v.title LIKE ?
                ORDER BY v.last_seen DESC
                LIMIT ?
            """, (f"%{query}%", max_results)).fetchall()
        
        download_links = []
        for row in rows:
            video_info = {
                "video_id": row["video_id"],
                "title": row["title"],
                "channel_title": row["channel_title"],
                "duration_sec": row["duration_sec"],
                "primary_genre": row["primary_genre"],
                "genre_confidence": row["genre_confidence"],
                "is_downloaded": row["audio_path"] is not None,
                "download_url": f"/download/{row['video_id']}" if row["audio_path"] else f"/api/download/{row['video_id']}",
                "youtube_url": f"https://www.youtube.com/watch?v={row['video_id']}",
                "downloaded_at": row["downloaded_at"]
            }
            download_links.append(video_info)
        
        return jsonify({
            "status": "success",
            "message": f"Найдено {len(download_links)} треков по запросу '{query}'",
            "query": query,
            "found": len(download_links),
            "download_links": download_links
        })
        
    except Exception as e:
        return jsonify({
            "status": "error", 
            "message": str(e)
        }), 500

@app.route('/api/search_links')
def api_search_links():
    """
    API endpoint для поиска треков и получения только ссылок (без скачивания)
    Пример: GET /api/search_links?query=moto%20x3m&max_results=10
    """
    try:
        query = request.args.get('query', '').strip()
        max_results = int(request.args.get('max_results', 10))
        
        if not query:
            return jsonify({
                "status": "error", 
                "message": "Параметр 'query' обязателен"
            }), 400
        
        # Выполняем поиск (опционально)
        # found = search_by_custom_query(query, max_results)
        
        # Получаем информацию о найденных видео (последние треки)
        from db import get_conn
        with get_conn() as con:
            rows = con.execute("""
                SELECT v.video_id, v.title, v.channel_title, v.duration_sec,
                       v.primary_genre, v.genre_confidence
                FROM videos v
                WHERE v.is_short = 1
                ORDER BY v.last_seen DESC
                LIMIT ?
            """, (max_results,)).fetchall()
        
        links = []
        for row in rows:
            video_info = {
                "video_id": row["video_id"],
                "title": row["title"],
                "channel_title": row["channel_title"],
                "duration_sec": row["duration_sec"],
                "primary_genre": row["primary_genre"],
                "genre_confidence": row["genre_confidence"],
                "youtube_url": f"https://www.youtube.com/watch?v={row['video_id']}",
                "download_url": f"http://localhost:5002/download/{row['video_id']}",
                "api_download_url": f"http://localhost:5002/api/download/{row['video_id']}"
            }
            links.append(video_info)
        
        return jsonify({
            "status": "success",
            "message": f"Найдено {len(links)} треков по запросу '{query}'",
            "query": query,
            "found": len(links),
            "links": links
        })
        
    except Exception as e:
        return jsonify({
            "status": "error", 
            "message": str(e)
        }), 500

@app.route('/api/download/<video_id>')
def api_download_info(video_id):
    """
    API endpoint для получения информации о скачивании конкретного трека
    Пример: GET /api/download/nSo6GM5ke7M
    """
    try:
        from db import get_conn
        with get_conn() as con:
            row = con.execute("""
                SELECT v.video_id, v.title, v.channel_title, v.duration_sec,
                       v.primary_genre, v.genre_confidence,
                       d.audio_path, d.downloaded_at
                FROM videos v
                LEFT JOIN downloads d ON v.video_id = d.video_id
                WHERE v.video_id = ?
            """, (video_id,)).fetchone()
        
        if not row:
            return jsonify({
                "status": "error",
                "message": "Трек не найден"
            }), 404
        
        video_info = {
            "video_id": row["video_id"],
            "title": row["title"],
            "channel_title": row["channel_title"],
            "duration_sec": row["duration_sec"],
            "primary_genre": row["primary_genre"],
            "genre_confidence": row["genre_confidence"],
            "is_downloaded": row["audio_path"] is not None,
            "youtube_url": f"https://www.youtube.com/watch?v={row['video_id']}",
            "download_url": f"http://localhost:5002/download/{row['video_id']}",
            "downloaded_at": row["downloaded_at"]
        }
        
        return jsonify({
            "status": "success",
            "video": video_info
        })
        
    except Exception as e:
        return jsonify({
            "status": "error", 
            "message": str(e)
        }), 500

@app.route('/api/direct_download/<video_id>')
def api_direct_download(video_id):
    """
    API endpoint для получения прямой ссылки на скачивание аудио (без локального хранения)
    Пример: GET /api/direct_download/nSo6GM5ke7M
    """
    try:
        import yt_dlp
        import tempfile
        import os
        
        # Получаем информацию о видео из базы
        from db import get_conn
        with get_conn() as con:
            row = con.execute("""
                SELECT v.video_id, v.title, v.channel_title, v.duration_sec
                FROM videos v
                WHERE v.video_id = ?
            """, (video_id,)).fetchone()
        
        if not row:
            return jsonify({
                "status": "error",
                "message": "Трек не найден"
            }), 404
        
        # Настройки yt-dlp для получения прямой ссылки
        ydl_opts = {
            "format": "bestaudio/best",
            "quiet": True,
            "no_warnings": True,
            "extract_flat": False,
        }
        
        url = f"https://www.youtube.com/watch?v={video_id}"
        
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=False)
            
            # Ищем лучший аудио формат
            audio_url = None
            audio_format = None
            
            if 'formats' in info:
                for fmt in info['formats']:
                    if fmt.get('acodec') != 'none' and fmt.get('vcodec') == 'none':
                        audio_url = fmt.get('url')
                        audio_format = fmt.get('ext', 'mp3')
                        break
            
            if not audio_url:
                return jsonify({
                    "status": "error",
                    "message": "Не удалось получить прямую ссылку на аудио"
                }), 500
        
        return jsonify({
            "status": "success",
            "video_id": video_id,
            "title": row["title"],
            "channel_title": row["channel_title"],
            "duration_sec": row["duration_sec"],
            "youtube_url": url,
            "direct_download_url": audio_url,
            "format": audio_format,
            "message": "Прямая ссылка на аудио получена"
        })
        
    except Exception as e:
        return jsonify({
            "status": "error", 
            "message": f"Ошибка получения прямой ссылки: {str(e)}"
        }), 500

@app.route('/api/search_direct_links')
def api_search_direct_links():
    """
    API endpoint для поиска треков и получения прямых ссылок на скачивание
    Пример: GET /api/search_direct_links?query=moto%20x3m&max_results=5
    """
    try:
        query = request.args.get('query', '').strip()
        max_results = int(request.args.get('max_results', 5))
        
        if not query:
            return jsonify({
                "status": "error", 
                "message": "Параметр 'query' обязателен"
            }), 400
        
        # Выполняем поиск через YouTube API и получаем результаты
        from search_trends import search_by_custom_query
        found_count = search_by_custom_query(query, max_results)
        
        # Получаем найденные видео с последней статистикой
        from db import get_conn
        with get_conn() as con:
            rows = con.execute("""
                SELECT v.video_id, v.title, v.channel_title, v.duration_sec,
                       v.primary_genre, v.genre_confidence,
                       s.view_count, s.like_count, s.comment_count, s.snapshot_date
                FROM videos v
                LEFT JOIN (
                    SELECT video_id, view_count, like_count, comment_count, snapshot_date,
                           ROW_NUMBER() OVER (PARTITION BY video_id ORDER BY snapshot_date DESC) as rn
                    FROM stats
                ) s ON v.video_id = s.video_id AND s.rn = 1
                WHERE v.is_short = 1 
                AND (v.title LIKE ? OR v.channel_title LIKE ?)
                ORDER BY v.last_seen DESC
                LIMIT ?
            """, (f'%{query}%', f'%{query}%', max_results)).fetchall()
        
        links = []
        for row in rows:
            video_info = {
                "video_id": row["video_id"],
                "title": row["title"],
                "channel_title": row["channel_title"],
                "duration_sec": row["duration_sec"],
                "primary_genre": row["primary_genre"],
                "genre_confidence": row["genre_confidence"],
                "youtube_url": f"https://www.youtube.com/watch?v={row['video_id']}",
                "direct_download_url": f"http://localhost:5002/api/direct_download/{row['video_id']}",
                "download_info_url": f"http://localhost:5002/api/download/{row['video_id']}",
                "stats": {
                    "view_count": row["view_count"] or 0,
                    "like_count": row["like_count"] or 0,
                    "comment_count": row["comment_count"] or 0,
                    "last_updated": row["snapshot_date"]
                }
            }
            links.append(video_info)
        
        return jsonify({
            "status": "success",
            "message": f"Найдено {len(links)} треков по запросу '{query}'",
            "query": query,
            "found": len(links),
            "links": links
        })
        
    except Exception as e:
        return jsonify({
            "status": "error", 
            "message": str(e)
        }), 500

@app.route('/api/search_and_download_force')
def api_search_and_download_force():
    """
    API endpoint для поиска и принудительного скачивания треков
    Пример: POST /api/search_and_download_force
    Body: {"query": "moto x3m", "max_results": 5, "download": true}
    """
    try:
        data = request.get_json()
        query = data.get('query', '').strip()
        max_results = int(data.get('max_results', 5))
        force_download = data.get('download', False)
        
        if not query:
            return jsonify({
                "status": "error", 
                "message": "Параметр 'query' обязателен"
            }), 400
        
        # Выполняем поиск
        found = search_by_custom_query(query, max_results)
        
        if found == 0:
            return jsonify({
                "status": "success",
                "message": f"По запросу '{query}' ничего не найдено",
                "query": query,
                "found": 0,
                "download_links": []
            })
        
        # Если нужно скачать, запускаем скачивание
        if force_download:
            from rank_shorts import rank_top_n
            from download_audio import download_audio_for
            
            # Получаем топ видео для скачивания
            top_videos = rank_top_n(max_results)
            video_ids = [v["video_id"] for v in top_videos]
            
            # Скачиваем аудио
            download_audio_for(video_ids)
        
        # Получаем обновленную информацию
        from db import get_conn
        with get_conn() as con:
            rows = con.execute("""
                SELECT v.video_id, v.title, v.channel_title, v.duration_sec,
                       v.primary_genre, v.genre_confidence,
                       d.audio_path, d.downloaded_at
                FROM videos v
                LEFT JOIN downloads d ON v.video_id = d.video_id
                WHERE v.is_short = 1
                ORDER BY v.last_seen DESC
                LIMIT ?
            """, (max_results,)).fetchall()
        
        download_links = []
        for row in rows:
            video_info = {
                "video_id": row["video_id"],
                "title": row["title"],
                "channel_title": row["channel_title"],
                "duration_sec": row["duration_sec"],
                "primary_genre": row["primary_genre"],
                "genre_confidence": row["genre_confidence"],
                "is_downloaded": row["audio_path"] is not None,
                "download_url": f"/download/{row['video_id']}" if row["audio_path"] else None,
                "youtube_url": f"https://www.youtube.com/watch?v={row['video_id']}",
                "downloaded_at": row["downloaded_at"]
            }
            download_links.append(video_info)
        
        return jsonify({
            "status": "success",
            "message": f"Найдено {len(download_links)} треков по запросу '{query}'" + 
                      (" и скачано" if force_download else ""),
            "query": query,
            "found": len(download_links),
            "downloaded": force_download,
            "download_links": download_links
        })
        
    except Exception as e:
        return jsonify({
            "status": "error", 
            "message": str(e)
        }), 500

if __name__ == '__main__':
    init_db()
    port = int(os.getenv('PORT', 5002))
    app.run(debug=False, host='0.0.0.0', port=port)
