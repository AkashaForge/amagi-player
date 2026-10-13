"""
Модуль сервиса интеграции с API Кинопоиска Unofficial.
Реализует парсинг метаданных фильмов и логику умного локального кэширования
графических ассетов (постеров) для экономии суточных лимитов запросов.
"""

import os
import requests
import json
import config

class KPService:
    """
    Бизнес-логика взаимодействия с кино-серверами и управления кэшем.
    """
    def __init__(self):
        # Извлекаем ключ напрямую из глобального конфига приложения
        self.api_key = getattr(config, "KP_API_KEY", "")
        self.base_url = "https://kinopoiskapiunofficial.tech"
        
        # Строго выверенная структура заголовков, идентичная спецификации API
        self.headers = {
            "X-API-KEY": str(self.api_key),
            "Content-Type": "application/json",
            "Accept": "application/json",
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
        }
        
        # Гарантируем наличие физической директории для хранения локального кэша
        os.makedirs(config.CACHE_DIR, exist_ok=True)

    def get_movie_data(self, kp_id: int) -> dict:
        """
        Получает полные метаданные фильма по его уникальному ID.
        Возвращает словарь с названием, годом, описанием и абсолютным путем к картинке.
        
        УМНОЕ КЭШИРОВАНИЕ: Если данные и обложка уже были скачаны ранее, сетевой запрос
        полностью блокируется, данные извлекаются локально, сохраняя суточные лимиты.
        """
        # Принудительно валидируем ID на случай передачи некорректного типа из UI
        try:
            clean_id = int(kp_id)
        except (ValueError, TypeError):
            print(f"[КРИТИЧЕСКАЯ ОШИБКА]: Передан невалидный ID фильма: {kp_id}")
            return {"title": "Некорректный ID", "year": "----", "description": "Ошибка приведения типов.", "cover_path": ""}

        # Формируем изолированные пути для кэширования ассетов
        local_cover_path = os.path.join(config.CACHE_DIR, f"{clean_id}.jpg")
        local_json_path = os.path.join(config.CACHE_DIR, f"{clean_id}.json")
        
        # 1. ПРОВЕРКА ЛОКАЛЬНОГО ДИСКОВОГО КЭША (Защита от флуда и сетевых ошибок)
        if os.path.exists(local_json_path):
            try:
                with open(local_json_path, "r", encoding="utf-8") as f:
                    cached_data = json.load(f)
                
                # Проверяем, существует ли картинка физически рядом с JSON-файлом
                if os.path.exists(local_cover_path):
                    cached_data["cover_path"] = local_cover_path
                else:
                    cached_data["cover_path"] = ""
                    
                print(f"[БЭКЕНД КЭШ]: Данные для фильма {clean_id} успешно извлечены из локального кэша.")
                return cached_data
            except Exception as cache_err:
                print(f"[КЭШ ПРЕДУПРЕЖДЕНИЕ]: Не удалось прочитать локальный кэш для ID {clean_id}: {cache_err}")
        
        # Автономный режим, если ключ авторизации по какой-то причине отсутствует
        if not self.api_key:
            return {
                "title": f"Фильм ID {clean_id}",
                "year": "----",
                "description": "Описание недоступно. Проверьте конфигурацию KP_API_KEY в вашей системе.",
                "cover_path": ""
            }

        # 2. ИНИЦИАЛИЗАЦИЯ СЕТЕВОГО ЗАПРОСА К СЕРВЕРУ API
        try:
            url = f"{self.base_url}/api/v2.2/films/{clean_id}"
            
            # Отправляем синхронный запрос с жестким лимитом ожидания ответа в 5 секунд
            response = requests.get(url, headers=self.headers, timeout=5)
            
            # Успешный ответ сервера (Код 200 OK)
            if response.status_code == 200:
                data = response.json()
                
                # Безопасный парсинг JSON с многоуровневыми фоллбэками для пустых значений (None)
                title = data.get("nameRu") or data.get("nameOriginal") or "Без названия"
                year = data.get("year") or "----"
                description = data.get("description") or "Описание фильма отсутствует в базе данных фонда."
                poster_url = data.get("posterUrlPreview") or data.get("posterUrl")
                
                # 3. ФИЗИЧЕСКОЕ СКАЧИВАНИЕ ГРАФИЧЕСКОГО АССЕТА
                if poster_url and not os.path.exists(local_cover_path):
                    try:
                        # Используем только User-Agent для загрузки статики с CDN серверов картинщика
                        img_headers = {"User-Agent": self.headers["User-Agent"]}
                        img_response = requests.get(poster_url, headers=img_headers, timeout=5)
                        
                        if img_response.status_code == 200:
                            with open(local_cover_path, "wb") as img_file:
                                img_file.write(img_response.content)
                            print(f"[БЭКЕНД КЭШ]: Графический ассет для фильма {clean_id} успешно сохранен на диск.")
                    except Exception as img_err:
                        print(f"[СЕТЕВАЯ ОШИБКА]: Не удалось загрузить постер для фильма {clean_id}: {img_err}")

                # Формируем финальную структуру ответа для UI-контроллеров
                movie_dict = {
                    "title": str(title),
                    "year": str(year),
                    "description": str(description),
                    "cover_path": local_cover_path if os.path.exists(local_cover_path) else ""
                }

                # Сериализуем и сохраняем метаданные на диск для последующих холодных запусков
                try:
                    with open(local_json_path, "w", encoding="utf-8") as json_file:
                        json.dump(movie_dict, json_file, ensure_ascii=False, indent=4)
                except Exception as json_err:
                    print(f"[КЭШ ОШИБКА]: Не удалось сериализовать метаданные JSON на диск: {json_err}")

                return movie_dict
            
            # Обработка нештатных ответов удаленного сервера
            else:
                print(f"[API ОШИБКА]: Сервер вернул код {response.status_code} для медиа-ресурса с ID {clean_id}")
                return {
                    "title": f"Элемент фонда {clean_id}", 
                    "year": "----", 
                    "description": f"Сервер Кинопоиска отклонил запрос. Статус-код ответа: {response.status_code}.", 
                    "cover_path": ""
                }

        # Полная изоляция бизнес-логики от вылетов при физическом отсутствии интернета
        except requests.RequestException as network_err:
            print(f"[СЕТЕВАЯ ОШИБКА БЭКЕНДА]: Таймаут соединения или обрыв связи: {network_err}")
            return {
                "title": f"Медиа файл {clean_id}", 
                "year": "----", 
                "description": "Сбой сетевого подключения. Проверьте доступность узлов фильтрации трафика.", 
                "cover_path": ""
            }
        except Exception as critical_err:
            print(f"[КРИТИЧЕСКАЯ ОШИБКА СЕРВИСА]: Непредвиденный сбой парсера: {critical_err}")
            return {
                "title": f"Ошибка {clean_id}", 
                "year": "----", 
                "description": "Аварийное прерывание выполнения операции в модуле интеграции.", 
                "cover_path": ""
            }
