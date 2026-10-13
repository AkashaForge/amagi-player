"""
Официальный проверочный скрипт сетевого слоя Amagi-Player.
Выполняет GET-запрос к API Кинопоиска Unofficial и верифицирует токен.
"""

import os
import sys

# Настройка путей поиска локальных модулей Python
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from services.kp_service import KPService

def start_backend_network_test():
    print("=" * 60)
    print("ЗАПУСК ОФИЦИАЛЬНОГО ТЕСТА API КИНОПОИСКА UNOFFICIAL")
    print("=" * 60)

    # Инициализация сетевого сервиса
    kp = KPService()
    test_id = 44745  # Культовый ID: Иван Васильевич меняет профессию
    
    print(f"Отправка GET-запроса для фильма ID {test_id}...")
    movie_data = kp.get_movie_data(test_id)
    
    print("\n[ОТВЕТ СЕРВЕРА]:")
    print(f" -> Название контента: {movie_data['title']}")
    print(f" -> Год производства:  {movie_data['year']}")
    print(f" -> Локальный кэш .jpg: {movie_data['cover_path']}")
    
    # Инженерная проверка скачивания файла на жесткий диск
    if movie_data['cover_path'] and os.path.exists(movie_data['cover_path']):
        print("\n СТАТУС: УСПЕХ! Сетевой слой полностью работоспособен.")
    else:
        print("\n СТАТУС: СБОЙ. Сервер не отдал картинку. Перепроверьте .env")
    print("=" * 60)

if __name__ == "__main__":
    start_backend_network_test()
