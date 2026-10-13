"""
Исполнительный файл интеграционного тестирования Amagi-Player.
Связывает визуальный OLED-интерфейс, виджет ленты и реальный бэкенд Кинопоиска.
"""

import sys
import os

# Автоматическая настройка путей для предотвращения ModuleNotFoundError
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from PyQt6.QtWidgets import QApplication, QVBoxLayout
from ui.main_window import MainWindow
from ui.widgets.feed_widget import MovieFeedWidget
from ui.widgets.card_widget import MovieCardWidget
from services.kp_service import KPService

def run_integrated_ui_test():
    # 1. Инициализируем графическое приложение Qt
    app = QApplication(sys.argv)
    window = MainWindow()
    
    # 2. Инициализируем рабочий сетевой бэкенд-сервис
    kp_backend = KPService()
    
    # 3. Создаем наш новый пафосный виджет ленты
    feed_widget = MovieFeedWidget(window.feed_page_placeholder)
    
    # Имитируем базу данных Вайтлиста (список разрешенных ID классики кино)
    whitelist_mock_ids = [
        44745,   # Иван Васильевич меняет профессию
        42664,   # Операция «Ы» и другие приключения Шурика
        582144,  # Sintel (Легальная инди-анимация Blender)
        462244,  # Tears of Steel (Свободная фантастика CC)
    ]
    
    # Дублируем список, чтобы забить сетку и проверить работу скрытого скролла
    whitelist_mock_ids = whitelist_mock_ids * 3
    
    print("=" * 60)
    print("[ИНТЕГРАЦИЯ]: Заполнение ленты реальными постерами Кинопоиска...")
    print("=" * 60)
    
    # 4. В цикле запрашиваем данные из интернета и создаем карточки
    for index, kp_id in enumerate(whitelist_mock_ids):
        # Бэкенд делает GET-запрос и проверяет локальный кэш картинок в data/cache
        movie_data = kp_backend.get_movie_data(kp_id)
        
        # Создаем карточку, передавая оригинальные названия, года и картинки
        card = MovieCardWidget(
            kp_id=kp_id, 
            title=movie_data["title"], 
            year=movie_data["year"], 
            cover_path=movie_data["cover_path"]
        )
        
        # Передаем карточку в адаптивную сетку нашей новой ленты
        feed_widget.add_card_to_grid(card, index)
        
    # Вставляем готовую ленту в layout главного окна
    placeholder_layout = QVBoxLayout(window.feed_page_placeholder)
    placeholder_layout.setContentsMargins(0, 0, 0, 0)
    placeholder_layout.addWidget(feed_widget)
    
    # Показываем нижний парящий ледяной остров истории (Liquid Glass)
    window.show_resume_bar(movie_id=44745, movie_title="Иван Васильевич меняет профессию")
    
    print("\n[ИНТЕГРАЦИЯ]: Интерфейс успешно собран. Запуск окна.")
    window.show()
    sys.exit(app.exec())

if __name__ == "__main__":
    run_integrated_ui_test()
