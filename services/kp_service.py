"""
Модуль сервиса интеграции с API Кинопоиска Unofficial.
Реализует парсинг метаданных фильмов и логику умного локального кэширования
графических ассетов (постеров) для экономии суточных лимитов запросов.
"""

import os
import requests
import config

class KPService:
    """
    Бизнес-логика взаимодействия с кино-серверами и управления кэшем.
    """
    def __init__(self):
        self.api_key = config.KP_API_KEY
        self.base_url = "https://kinopoiskapiunofficial.tech"
        
        # Заголовки авторизации, требуемые сервером Кинопоиска Unofficial
        self.headers = {
            "X-API-KEY": self.api_key,
            "Content-Type": "application/json"
        }
        
        # Гарантируем, что физическая папка для кэша картинок существует на диске
        os.makedirs(config.CACHE_DIR, exist_ok=True)

    def get_movie_data(self, kp_id: int) -> dict:
        """
        Получает полные метаданные фильма по его уникальному ID.
        Возвращает словарь с названием, годом, описанием и абсолютным путем к картинке.
        
        УМНОЕ КЭШИРОВАНИЕ: Если обложка уже была скачана ранее, сетевой запрос
        блокируется, данные извлекаются локально, сохраняя бесплатные лимиты.
        """
        # Формируем целевой путь, где должна лежать скачанная картинка
        local_cover_path = os.path.join(config.CACHE_DIR, f"{kp_id}.jpg")
        
        # Если API-ключ не задан в .env, переходим в автономный текстовый режим
        if not self.api_key:
            return {
                "title": f"Фильм ID {kp_id}",
                "year": "----",
                "description": "Описание недоступно. Вставьте API-ключ в файл .env",
                "cover_path": ""
            }

        try:
            # 1. СЕТЕВОЙ ЗАПРОС К КИНОПОИСКУ
            url = f"{self.base_url}/{kp_id}"
            response = requests.get(url, headers=self.headers, timeout=5)
            
            if response.status_code == 200:
                data = response.json()
                
                # Извлекаем данные, страхуясь от пустых значений (None)
                title = data.get("nameRu") or data.get("nameOriginal") or "Без названия"
                year = data.get("year") or "----"
                description = data.get("description") or "Описание фильма отсутствует."
                poster_url = data.get("posterUrlPreview") # Облегченная мини-версия обложки для сетки
                
                # 2. ФИЗИЧЕСКОЕ СКАЧИВАНИЕ ОБЛОЖКИ В КЭШ
                if poster_url and not os.path.exists(local_cover_path):
                    img_response = requests.get(poster_url, timeout=5)
                    if img_response.status_code == 200:
                        # Открываем бинарный поток и записываем байты картинки на жесткий диск
                        with open(local_cover_path, "wb") as f:
                            f.write(img_response.content)
                            print(f"[БЭКЕНД КЭШ]: Обложка для фильма {kp_id} успешно сохранена на диск.")

                return {
                    "title": title,
                    "year": str(year),
                    "description": description,
                    "cover_path": local_cover_path if os.path.exists(local_cover_path) else ""
                }
            else:
                print(f"[API ОШИБКА]: Сервер вернул код {response.status_code} для ID {kp_id}")
                return {"title": f"Элемент фонда {kp_id}", "year": "----", "description": "Ошибка авторизации или лимитов API.", "cover_path": ""}

        except Exception as e:
            # Полная защита от вылета программы при отсутствии интернета
            print(f"[СЕТЕВАЯ ОШИБКА БЭКЕНДА]: {e}")
            return {"title": f"Медиа файл {kp_id}", "year": "----", "description": "Сбой сетевого подключения.", "cover_path": ""}

