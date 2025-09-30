import re
from typing import List, Dict, Optional

# Ключевые слова для определения музыкальных жанров
GENRE_KEYWORDS = {
    "hip_hop": [
        "hip hop", "rap", "trap", "drill", "beat", "flow", "bars", "freestyle",
        "mixtape", "album", "verse", "hook", "rhyme", "lyrics", "mc", "dj"
    ],
    "pop": [
        "pop", "mainstream", "hit", "chart", "radio", "catchy", "melody", "chorus",
        "single", "top 40", "commercial", "mainstream pop"
    ],
    "electronic": [
        "electronic", "edm", "dubstep", "house", "techno", "trance", "drum", "bass",
        "synth", "beat", "drop", "remix", "mix", "dj set", "electronic music"
    ],
    "rock": [
        "rock", "metal", "punk", "alternative", "indie", "guitar", "drums", "band",
        "concert", "live", "acoustic", "electric", "riff", "solo"
    ],
    "rnb": [
        "r&b", "rnb", "soul", "funk", "blues", "jazz", "smooth", "vocal", "singer",
        "melody", "harmony", "groove", "rhythm"
    ],
    "country": [
        "country", "folk", "bluegrass", "acoustic", "guitar", "banjo", "fiddle",
        "western", "southern", "rural", "cowboy", "honky tonk"
    ],
    "latin": [
        "latin", "reggaeton", "salsa", "bachata", "merengue", "cumbia", "spanish",
        "latino", "hispanic", "tropical", "caribbean"
    ],
    "classical": [
        "classical", "orchestra", "symphony", "piano", "violin", "cello", "opera",
        "chamber", "baroque", "romantic", "composer", "conductor"
    ],
    "jazz": [
        "jazz", "blues", "swing", "bebop", "fusion", "improvisation", "saxophone",
        "trumpet", "piano", "bass", "drums", "combo", "big band"
    ],
    "reggae": [
        "reggae", "dancehall", "ska", "rocksteady", "jamaican", "island", "tropical",
        "bob marley", "rasta", "dub", "roots"
    ]
}

def analyze_genre(title: str, description: str = "", tags: List[str] = None) -> Dict[str, float]:
    """
    Анализирует жанр на основе названия, описания и тегов
    Возвращает словарь с вероятностями для каждого жанра
    """
    if tags is None:
        tags = []
    
    # Объединяем весь текст для анализа
    text = f"{title} {description} {' '.join(tags)}".lower()
    
    genre_scores = {}
    
    for genre, keywords in GENRE_KEYWORDS.items():
        score = 0
        for keyword in keywords:
            # Простой подсчет вхождений ключевых слов
            count = text.count(keyword.lower())
            score += count
        
        # Нормализуем по длине текста
        text_length = len(text.split())
        if text_length > 0:
            genre_scores[genre] = score / text_length
        else:
            genre_scores[genre] = 0
    
    return genre_scores

def get_primary_genre(genre_scores: Dict[str, float]) -> Optional[str]:
    """Возвращает основной жанр с наибольшей вероятностью"""
    if not genre_scores:
        return None
    
    max_score = max(genre_scores.values())
    if max_score == 0:
        return None
    
    for genre, score in genre_scores.items():
        if score == max_score:
            return genre
    
    return None

def get_genre_confidence(genre_scores: Dict[str, float]) -> float:
    """Возвращает уверенность в определении жанра (0-1)"""
    if not genre_scores:
        return 0.0
    
    scores = list(genre_scores.values())
    if not scores:
        return 0.0
    
    # Уверенность = разница между первым и вторым по величине скором
    sorted_scores = sorted(scores, reverse=True)
    if len(sorted_scores) < 2:
        return sorted_scores[0] if sorted_scores else 0.0
    
    confidence = sorted_scores[0] - sorted_scores[1]
    return min(confidence, 1.0)

def filter_by_genre(videos: List[Dict], target_genres: List[str], min_confidence: float = 0.1) -> List[Dict]:
    """
    Фильтрует видео по жанрам
    """
    filtered = []
    
    for video in videos:
        title = video.get('title', '')
        description = video.get('description', '')
        tags = video.get('tags', [])
        
        genre_scores = analyze_genre(title, description, tags)
        primary_genre = get_primary_genre(genre_scores)
        confidence = get_genre_confidence(genre_scores)
        
        # Добавляем информацию о жанре в видео
        video['genre_scores'] = genre_scores
        video['primary_genre'] = primary_genre
        video['genre_confidence'] = confidence
        
        # Проверяем, подходит ли жанр
        if primary_genre in target_genres and confidence >= min_confidence:
            filtered.append(video)
    
    return filtered

def get_genre_statistics(videos: List[Dict]) -> Dict[str, int]:
    """Возвращает статистику по жанрам"""
    stats = {}
    
    for video in videos:
        primary_genre = video.get('primary_genre')
        if primary_genre:
            stats[primary_genre] = stats.get(primary_genre, 0) + 1
    
    return stats

# Популярные поисковые запросы по жанрам
GENRE_SEARCH_QUERIES = {
    "hip_hop": [
        "hip hop shorts", "rap music shorts", "trap beat shorts", "drill music shorts",
        "hip hop viral", "rap trending", "trap music viral", "hip hop beat"
    ],
    "pop": [
        "pop music shorts", "mainstream pop shorts", "pop hit shorts", "chart music shorts",
        "pop viral", "mainstream trending", "pop music viral", "hit song shorts"
    ],
    "electronic": [
        "edm shorts", "electronic music shorts", "dubstep shorts", "house music shorts",
        "edm viral", "electronic trending", "dubstep viral", "house music viral"
    ],
    "rock": [
        "rock music shorts", "metal shorts", "punk shorts", "alternative rock shorts",
        "rock viral", "metal trending", "punk viral", "rock music viral"
    ],
    "rnb": [
        "r&b shorts", "rnb shorts", "soul music shorts", "funk shorts",
        "r&b viral", "soul trending", "rnb viral", "soul music viral"
    ]
}

def get_genre_search_queries(genres: List[str]) -> List[str]:
    """Возвращает поисковые запросы для указанных жанров"""
    queries = []
    for genre in genres:
        if genre in GENRE_SEARCH_QUERIES:
            queries.extend(GENRE_SEARCH_QUERIES[genre])
    return queries
