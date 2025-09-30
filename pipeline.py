from config import TOP_N_DOWNLOAD
from fetch_shorts import fetch_and_store
from search_trends import search_trending_sounds
from rank_shorts import rank_top_n
from download_audio import download_audio_for

def run_pipeline():
    # 1) получить популярные Shorts (US) и записать метрики
    print("=== Получение популярных Shorts ===")
    fetch_and_store()
    
    # 2) поиск трендовых звуков по ключевым словам
    print("=== Поиск трендовых звуков ===")
    search_trending_sounds()

    # 3) отранжировать и выбрать топ N (по простому TrendScore)
    print("=== Ранжирование и отбор ===")
    top = rank_top_n(TOP_N_DOWNLOAD)
    print(f"Найдено {len(top)} трендовых треков")

    # 4) больше не скачиваем локально - только прямые ссылки
    print("=== Готово! Используйте API для получения прямых ссылок ===")

if __name__ == "__main__":
    run_pipeline()
