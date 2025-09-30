# YouTube Shorts Parser

Веб-приложение для парсинга, анализа и скачивания YouTube Shorts с музыкальным контентом.

## 🚀 Развертывание на Railway

### 1. Подготовка к развертыванию

1. Убедитесь, что у вас есть YouTube Data API ключ
2. Создайте репозиторий на GitHub
3. Загрузите код в репозиторий

### 2. Настройка Railway

1. Зайдите на [Railway.app](https://railway.app)
2. Войдите через GitHub
3. Нажмите "New Project" → "Deploy from GitHub repo"
4. Выберите ваш репозиторий

### 3. Переменные окружения

В настройках проекта Railway добавьте следующие переменные:

```
YOUTUBE_API_KEY=ваш_youtube_api_ключ
REGION_CODE=US
SHORTS_MAX_SECONDS=60
TOP_N_DOWNLOAD=10
MEDIA_DIR=media
DB_PATH=data/shorts.db
```

### 4. Запуск

Railway автоматически развернет приложение. URL будет доступен в панели управления.

## 📋 API Endpoints

- `GET /` - Главная страница
- `GET /api/files` - Список всех файлов
- `GET /api/trending` - Трендовые Shorts
- `GET /api/search_and_download?query=...` - Поиск и скачивание
- `GET /api/search_direct_links?query=...` - Прямые ссылки
- `GET /api/genres` - Статистика по жанрам
- `GET /download/<video_id>` - Скачивание файла

## 🛠 Локальная разработка

1. Клонируйте репозиторий
2. Создайте виртуальное окружение: `python3 -m venv venv`
3. Активируйте окружение: `source venv/bin/activate`
4. Установите зависимости: `pip install -r requirements.txt`
5. Создайте файл `.env` с переменными окружения
6. Запустите: `python app.py`

## 📁 Структура проекта

```
├── app.py              # Основное Flask приложение
├── config.py           # Конфигурация
├── db.py              # Работа с базой данных
├── pipeline.py        # Основной пайплайн парсинга
├── search_trends.py   # Поиск трендов
├── rank_shorts.py     # Ранжирование Shorts
├── download_audio.py  # Скачивание аудио
├── genre_analyzer.py  # Анализ жанров
├── templates/         # HTML шаблоны
├── data/             # База данных
└── media/            # Скачанные файлы
```
