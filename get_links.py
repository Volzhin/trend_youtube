#!/usr/bin/env python3
"""
Получение ссылок для скачивания треков через API
Использование: python get_links.py "moto x3m" --max 5
"""

import requests
import argparse
import json

BASE_URL = "http://localhost:5002"

def get_download_links(query, max_results=5):
    """Получение ссылок для скачивания треков"""
    print(f"🔍 Поиск: '{query}'")
    print(f"📊 Максимум результатов: {max_results}")
    print("-" * 50)
    
    url = f"{BASE_URL}/api/search_links"
    params = {
        "query": query,
        "max_results": max_results
    }
    
    try:
        response = requests.get(url, params=params, timeout=30)
        result = response.json()
        
        if result.get("status") != "success":
            print(f"❌ Ошибка: {result.get('message', 'Неизвестная ошибка')}")
            return
        
        print(f"✅ {result['message']}")
        print()
        
        if not result.get('links'):
            print("❌ Треки не найдены")
            return
        
        # Выводим найденные треки с ссылками
        for i, track in enumerate(result['links'], 1):
            print(f"{i:2d}. {track['title']}")
            print(f"    Канал: {track['channel_title']}")
            print(f"    Длительность: {track['duration_sec']} сек")
            
            if track.get('primary_genre'):
                print(f"    Жанр: {track['primary_genre']} (уверенность: {track['genre_confidence']:.2f})")
            
            print(f"    🎥 YouTube: {track['youtube_url']}")
            print(f"    ⬇️ Скачать: {track['download_url']}")
            print(f"    🔗 API: {track['api_download_url']}")
            print()
        
        # Сохраняем ссылки в файл
        save_links_to_file(result['links'], query)
        
    except Exception as e:
        print(f"❌ Ошибка: {e}")

def save_links_to_file(links, query):
    """Сохранение ссылок в файл"""
    filename = f"links_{query.replace(' ', '_')}.txt"
    
    with open(filename, 'w', encoding='utf-8') as f:
        f.write(f"Ссылки для скачивания треков по запросу: {query}\n")
        f.write("=" * 60 + "\n\n")
        
        for i, track in enumerate(links, 1):
            f.write(f"{i}. {track['title']}\n")
            f.write(f"   Канал: {track['channel_title']}\n")
            f.write(f"   Длительность: {track['duration_sec']} сек\n")
            f.write(f"   YouTube: {track['youtube_url']}\n")
            f.write(f"   Скачать: {track['download_url']}\n")
            f.write(f"   API: {track['api_download_url']}\n")
            f.write("\n")
    
    print(f"💾 Ссылки сохранены в файл: {filename}")

def get_single_track_info(video_id):
    """Получение информации о конкретном треке"""
    url = f"{BASE_URL}/api/download/{video_id}"
    
    try:
        response = requests.get(url, timeout=30)
        result = response.json()
        
        if result.get("status") != "success":
            print(f"❌ Ошибка: {result.get('message', 'Неизвестная ошибка')}")
            return
        
        track = result['video']
        print(f"🎵 {track['title']}")
        print(f"   Канал: {track['channel_title']}")
        print(f"   Длительность: {track['duration_sec']} сек")
        print(f"   Скачан: {'✅' if track['is_downloaded'] else '❌'}")
        print(f"   YouTube: {track['youtube_url']}")
        print(f"   Скачать: {track['download_url']}")
        
    except Exception as e:
        print(f"❌ Ошибка: {e}")

def main():
    parser = argparse.ArgumentParser(description="Получение ссылок для скачивания треков")
    parser.add_argument("query", help="Поисковый запрос")
    parser.add_argument("-m", "--max", type=int, default=5, 
                       help="Максимальное количество результатов (по умолчанию: 5)")
    parser.add_argument("--track-id", help="Получить информацию о конкретном треке по video_id")
    
    args = parser.parse_args()
    
    # Проверяем доступность сервера
    try:
        response = requests.get(f"{BASE_URL}/api/genres", timeout=5)
        if response.status_code != 200:
            print("❌ Сервер недоступен")
            return
    except:
        print("❌ Сервер недоступен. Запустите: python app.py")
        return
    
    if args.track_id:
        # Получаем информацию о конкретном треке
        get_single_track_info(args.track_id)
    else:
        # Поиск треков
        get_download_links(args.query, args.max)

if __name__ == "__main__":
    main()
