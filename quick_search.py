#!/usr/bin/env python3
"""
Быстрый поиск и скачивание треков через API
Использование: python quick_search.py "moto x3m" --download
"""

import requests
import argparse
import sys
import os
from urllib.parse import quote

BASE_URL = "http://localhost:5001"

def search_tracks(query, max_results=5, download=False):
    """Поиск треков по запросу"""
    print(f"🔍 Поиск: '{query}'")
    print(f"📊 Максимум результатов: {max_results}")
    print(f"⬇️ Скачивание: {'Да' if download else 'Нет'}")
    print("-" * 50)
    
    if download:
        # Используем API с принудительным скачиванием
        url = f"{BASE_URL}/api/search_and_download_force"
        data = {
            "query": query,
            "max_results": max_results,
            "download": True
        }
        
        try:
            response = requests.post(url, json=data, timeout=60)
            result = response.json()
        except requests.exceptions.RequestException as e:
            print(f"❌ Ошибка запроса: {e}")
            return
    else:
        # Обычный поиск
        url = f"{BASE_URL}/api/search_and_download"
        params = {
            "query": query,
            "max_results": max_results
        }
        
        try:
            response = requests.get(url, params=params, timeout=30)
            result = response.json()
        except requests.exceptions.RequestException as e:
            print(f"❌ Ошибка запроса: {e}")
            return
    
    if result.get("status") != "success":
        print(f"❌ Ошибка: {result.get('message', 'Неизвестная ошибка')}")
        return
    
    print(f"✅ {result['message']}")
    print()
    
    if not result.get('download_links'):
        print("❌ Треки не найдены")
        return
    
    # Выводим найденные треки
    for i, track in enumerate(result['download_links'], 1):
        print(f"{i:2d}. {track['title']}")
        print(f"    Канал: {track['channel_title']}")
        print(f"    Длительность: {track['duration_sec']} сек")
        
        if track.get('primary_genre'):
            print(f"    Жанр: {track['primary_genre']} (уверенность: {track['genre_confidence']:.2f})")
        
        if track['is_downloaded']:
            print(f"    ✅ Скачан")
            if track['download_url']:
                print(f"    📥 Ссылка: {BASE_URL}{track['download_url']}")
        else:
            print(f"    ❌ Не скачан")
        
        print(f"    🎥 YouTube: {track['youtube_url']}")
        print()

def download_track(video_id, filename=None):
    """Скачивание конкретного трека"""
    if not filename:
        filename = f"{video_id}.mp3"
    
    url = f"{BASE_URL}/download/{video_id}"
    
    try:
        print(f"⬇️ Скачивание {video_id}...")
        response = requests.get(url, stream=True)
        
        if response.status_code == 200:
            with open(filename, 'wb') as f:
                for chunk in response.iter_content(chunk_size=8192):
                    f.write(chunk)
            print(f"✅ Скачано: {filename}")
        else:
            print(f"❌ Ошибка скачивания: {response.status_code}")
            
    except Exception as e:
        print(f"❌ Ошибка: {e}")

def main():
    parser = argparse.ArgumentParser(description="Быстрый поиск и скачивание треков")
    parser.add_argument("query", help="Поисковый запрос")
    parser.add_argument("-n", "--max-results", type=int, default=5, 
                       help="Максимальное количество результатов (по умолчанию: 5)")
    parser.add_argument("-d", "--download", action="store_true", 
                       help="Принудительно скачать найденные треки")
    parser.add_argument("--download-id", help="Скачать конкретный трек по video_id")
    
    args = parser.parse_args()
    
    # Проверяем доступность сервера
    try:
        response = requests.get(f"{BASE_URL}/api/genres", timeout=5)
        if response.status_code != 200:
            print("❌ Сервер недоступен")
            sys.exit(1)
    except:
        print("❌ Сервер недоступен. Запустите: python app.py")
        sys.exit(1)
    
    if args.download_id:
        # Скачиваем конкретный трек
        download_track(args.download_id)
    else:
        # Поиск треков
        search_tracks(args.query, args.max_results, args.download)

if __name__ == "__main__":
    main()
