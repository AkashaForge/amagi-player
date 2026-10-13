"""
Запускной файл тестирования визуальной оболочки приложения Amagi-Player.
"""

import sys
from PyQt6.QtWidgets import QApplication, QLabel, QVBoxLayout
from ui.main_window import MainWindow

def run_visual_layout_test():
    # 1. Инициализируем графическое приложение Qt
    app = QApplication(sys.argv)
    
    # 2. Создаем экземпляр главного окна
    window = MainWindow()
    
    # Наполняем страницы-заглушки стопки виджетов временным текстом
    # Страница 0: Лента контента
    feed_layout = QVBoxLayout(window.feed_page_placeholder)
    lbl_feed = QLabel("ЗДЕСЬ БУДЕТ СЕТКА КАРТОЧЕК С ФИЛЬМАМИ И ОБЛОЖКАМИ", window.feed_page_placeholder)
    lbl_feed.setStyleSheet("color: #666666; font-size: 16px; font-weight: bold;")
    lbl_feed.setAlignment(Qt.AlignmentFlag.AlignCenter)
    feed_layout.addWidget(lbl_feed)
    
    # Страница 1: Настройки приложения
    settings_layout = QVBoxLayout(window.settings_page_placeholder)
    lbl_settings = QLabel("ОКНО НАСТРОЕК SQLite (КЛИКНИТЕ 'СМЕНИТЬ ТЕМУ' ИЛИ ЗАКРОЙТЕ ОКНО)", window.settings_page_placeholder)
    lbl_settings.setStyleSheet("color: #FF6B00; font-size: 16px; font-weight: bold;")
    lbl_settings.setAlignment(Qt.AlignmentFlag.AlignCenter)
    settings_layout.addWidget(lbl_settings)
    
    # ЭМУЛЯЦИЯ БД: Командуем плашке всплыть, подставив тестовые данные классики фонда
    window.show_resume_bar(movie_id=44745, movie_title="Иван Васильевич меняет профессию")
    
    # 3. Выводим окно на экран компьютера
    window.show()
    
    # Передаем управление бесконечному циклу обработки событий PyQt6
    sys.exit(app.exec())

if __name__ == "__main__":
    run_visual_layout_test()
