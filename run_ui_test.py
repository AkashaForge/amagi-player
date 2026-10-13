import sys
import os

# Явно добавляем корень проекта в пути импорта
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from PyQt6.QtWidgets import QApplication
from ui.main_window import MainWindow
from ui.widgets.card_widget import MovieCardWidget
from services.kp_service import KPService

def run_integrated_ui_test():
    app = QApplication(sys.argv)
    window = MainWindow()
    kp_backend = KPService()
    
    # Берем готовую страницу ленты напрямую из главного окна (уже настроенного нами)
    feed_widget = window.feed_page 
    
    # 1. СЛОТ ПЕРЕХОДА НА ЭКРАН ОПИСАНИЯ ПРИ КЛИКЕ НА КАРТОЧКУ
    def on_movie_card_clicked(kp_id):
        print(f"[ИНТЕГРАЦИЯ СИГНАЛОВ]: Клик по фильму ID {kp_id}. Запрос к API...")
        data = kp_backend.get_movie_data(kp_id)
        
        # Наполняем экран описания реальными данными из вашего сервиса kp_service
        window.details_page.set_movie_context(
            kp_id=kp_id,
            title=data["title"],
            year=data["year"],
            description="Культурное наследие фонда общественного достояния. Документальные архивы и некоммерческий кинематограф.",
            cover_path=data["cover_path"]
        )
        # Переключаем стек на индекс 1 (Экран деталей фильма)
        window.screen_stack.setCurrentIndex(1)

    # 2. СЛОТ ПЕРЕХОДА В ПЛЕЕР
    def on_start_streaming(kp_id):
        print(f"[ИНТЕГРАЦИЯ СИГНАЛОВ]: Старт P2P потока для ID {kp_id}. Переход в плеер.")
        window.screen_stack.setCurrentIndex(2) # Индекс 2: Видеоплеер

    # 3. СЛОТ ВОЗВРАТА ИЗ ПЛЕЕРА ИЛИ ДЕТАЛЕЙ
    def on_back_to_feed():
        window.screen_stack.setCurrentIndex(0) # Индекс 0: Обратно к общей ленте

    # Подключаем сигналы к методам переключения экранов
    window.details_page.start_streaming_requested.connect(on_start_streaming)
    window.details_page.back_to_feed_requested.connect(on_back_to_feed)
    window.player_page.close_player_requested.connect(lambda secs: on_back_to_feed())

    # Генерируем тестовую сетку фильмов (Берем ваши тестовые ID)
    whitelist_mock_ids = [44745, 42664, 582144, 462244] * 2
    feed_widget.clear_grid() # Чистим сетку перед заполнением
    
    for index, kp_id in enumerate(whitelist_mock_ids):
        movie_data = kp_backend.get_movie_data(kp_id)
        card = MovieCardWidget(
            kp_id=kp_id, 
            title=movie_data["title"], 
            year=movie_data["year"], 
            cover_path=movie_data["cover_path"]
        )
        
        # Связываем сигнал клика по кнопке карточки с функцией открытия деталей
        card.play_requested.connect(on_movie_card_clicked)
        feed_widget.add_card_to_grid(card, index)
        
    window.show()
    sys.exit(app.exec())

# Главная точка входа, которая принудительно заставит скрипт выполниться
if __name__ == "__main__":
    run_integrated_ui_test()

