#!/usr/bin/env python3
"""
Получение прямых ссылок на скачивание аудио (без локального хранения)
Использование: python get_direct_links.py "moto x3m" --max 5
"""

import requests
import argparse
import json

BASE_URL = "http://localhost:5002"

def get_direct_links(query, max_results=5):
    """Получение прямых ссылок на скачивание аудио"""
    print(f"🔍 Поиск: '{query}'")
    print(f"📊 Максимум результатов: {max_results}")
    print("-" * 50)
    
    url = f"{BASE_URL}/api/search_direct_links"
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
        
        # Выводим найденные треки с прямыми ссылками
        for i, track in enumerate(result['links'], 1):
            print(f"{i:2d}. {track['title']}")
            print(f"    Канал: {track['channel_title']}")
            print(f"    Длительность: {track['duration_sec']} сек")
            
            if track.get('primary_genre'):
                print(f"    Жанр: {track['primary_genre']} (уверенность: {track['genre_confidence']:.2f})")
            
            print(f"    🎥 YouTube: {track['youtube_url']}")
            print(f"    🔗 Прямая ссылка: {track['direct_download_url']}")
            print()
        
        # Сохраняем ссылки в файл
        save_direct_links_to_file(result['links'], query)
        
    except Exception as e:
        print(f"❌ Ошибка: {e}")

def get_single_direct_link(video_id):
    """Получение прямой ссылки на конкретный трек"""
    url = f"{BASE_URL}/api/direct_download/{video_id}"
    
    try:
        response = requests.get(url, timeout=30)
        result = response.json()
        
        if result.get("status") != "success":
            print(f"❌ Ошибка: {result.get('message', 'Неизвестная ошибка')}")
            return
        
        track = result
        print(f"🎵 {track['title']}")
        print(f"   Канал: {track['channel_title']}")
        print(f"   Длительность: {track['duration_sec']} сек")
        print(f"   Формат: {track['format']}")
        print(f"   YouTube: {track['youtube_url']}")
        print(f"   🔗 Прямая ссылка: {track['direct_download_url']}")
        
        # Сохраняем прямую ссылку в файл
        filename = f"direct_link_{video_id}.txt"
        with open(filename, 'w', encoding='utf-8') as f:
            f.write(f"Прямая ссылка на аудио: {track['title']}\n")
            f.write("=" * 60 + "\n\n")
            f.write(f"Video ID: {video_id}\n")
            f.write(f"Название: {track['title']}\n")
            f.write(f"Канал: {track['channel_title']}\n")
            f.write(f"Длительность: {track['duration_sec']} сек\n")
            f.write(f"Формат: {track['format']}\n")
            f.write(f"YouTube: {track['youtube_url']}\n")
            f.write(f"Прямая ссылка: {track['direct_download_url']}\n")
        
        print(f"💾 Прямая ссылка сохранена в файл: {filename}")
        
    except Exception as e:
        print(f"❌ Ошибка: {e}")

def save_direct_links_to_file(links, query):
    """Сохранение прямых ссылок в файл"""
    filename = f"direct_links_{query.replace(' ', '_')}.txt"
    
    with open(filename, 'w', encoding='utf-8') as f:
        f.write(f"Прямые ссылки на аудио по запросу: {query}\n")
        f.write("=" * 60 + "\n\n")
        
        for i, track in enumerate(links, 1):
            f.write(f"{i}. {track['title']}\n")
            f.write(f"   Канал: {track['channel_title']}\n")
            f.write(f"   Длительность: {track['duration_sec']} сек\n")
            f.write(f"   YouTube: {track['youtube_url']}\n")
            f.write(f"   Прямая ссылка: {track['direct_download_url']}\n")
            f.write("\n")
    
    print(f"💾 Прямые ссылки сохранены в файл: {filename}")

def download_with_direct_link(video_id, output_filename=None):
    """Скачивание аудио по прямой ссылке"""
    if not output_filename:
        output_filename = f"{video_id}.mp3"
    
    # Получаем прямую ссылку
    url = f"{BASE_URL}/api/direct_download/{video_id}"
    
    try:
        response = requests.get(url, timeout=30)
        result = response.json()
        
        if result.get("status") != "success":
            print(f"❌ Ошибка получения ссылки: {result.get('message')}")
            return
        
        direct_url = result['direct_download_url']
        print(f"⬇️ Скачивание {result['title']}...")
        
        # Скачиваем по прямой ссылке
        audio_response = requests.get(direct_url, stream=True, timeout=60)
        
        if audio_response.status_code == 200:
            with open(output_filename, 'wb') as f:
                for chunk in audio_response.iter_content(chunk_size=8192):
                    f.write(chunk)
            print(f"✅ Скачано: {output_filename}")
        else:
            print(f"❌ Ошибка скачивания: {audio_response.status_code}")
            
    except Exception as e:
        print(f"❌ Ошибка: {e}")

def main():
    parser = argparse.ArgumentParser(description="Получение прямых ссылок на скачивание аудио")
    parser.add_argument("query", nargs='?', help="Поисковый запрос")
    parser.add_argument("-m", "--max", type=int, default=5, 
                       help="Максимальное количество результатов (по умолчанию: 5)")
    parser.add_argument("--track-id", help="Получить прямую ссылку для конкретного трека по video_id")
    parser.add_argument("--download", help="Скачать аудио по video_id")
    parser.add_argument("--output", help="Имя выходного файла для скачивания")
    
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
    
    if args.download:
        # Скачиваем аудио по прямой ссылке
        download_with_direct_link(args.download, args.output)
    elif args.track_id:
        # Получаем прямую ссылку для конкретного трека
        get_single_direct_link(args.track_id)
    elif args.query:
        # Поиск треков
        get_direct_links(args.query, args.max)
    else:
        print("❌ Укажите запрос для поиска или --track-id для конкретного трека")
        print("Примеры:")
        print("  python get_direct_links.py 'moto x3m' --max 3")
        print("  python get_direct_links.py --track-id Axwi1s7MIDo")
        print("  python get_direct_links.py --download Axwi1s7MIDo --output track.mp3")

if __name__ == "__main__":
    main()
