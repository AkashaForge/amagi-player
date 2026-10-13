"""
Исполнительный скрипт изолированного тестирования сетевого слоя Кинопоиска.
"""

import os
import sys

# Прописываем пути, чтобы Python не ругался на локальные импорты модуля services
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from services.kp_service import KPService

def start_backend_network_test():
    print("=" * 60)
    print("ТЕСТ СЕТЕВОГО СЛУЖЕБНОГО МОДУЛЯ КИНОПОИСКА Unofficial")
    print("=" * 60)

    # Инициализируем созданный сервис
    kp = KPService()
    test_id = 44745
    
    print(f"Отправляем запрос к API для ID {test_id}...")
    movie_data = kp.get_movie_data(test_id)
    
    print("\n[РЕЗУЛЬТАТ ОТВЕТА СЕРВЕРА]:")
    print(f" -> Название фильма: {movie_data['title']}")
    print(f" -> Год производства: {movie_data['year']}")
    print(f" -> Путь к сохраненной картинке: {movie_data['cover_path']}")
    
    # Проверяем, физически ли файл скачался на жесткий диск вашего ПК в data/cache/
    if movie_data['cover_path'] and os.path.exists(movie_data['cover_path']):
        print("\n УСПЕХ: Бэкенд-сервис успешно забрал данные из интернета и закэшировал постер на диск!")
    else:
        print("\n СБОЙ: Данные не получены. Проверьте правильность токена в файле .env.")
    print("=" * 60)

if __name__ == "__main__":
    current_dir = os.path.dirname(os.path.abspath(__file__))
    start_backend_network_test()
