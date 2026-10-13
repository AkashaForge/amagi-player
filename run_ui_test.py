import sys
import os

sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from PyQt6.QtWidgets import QApplication, QVBoxLayout
from ui.main_window import MainWindow
from ui.widgets.feed_widget import MovieFeedWidget
from ui.widgets.card_widget import MovieCardWidget
from services.kp_service import KPService

def run_integrated_ui_test():
    app = QApplication(sys.argv)
    window = MainWindow()
    kp_backend = KPService()
    
    feed_widget = MovieFeedWidget(window.feed_page_placeholder)
    
    # 1. СЛОТ ПЕРЕХОДА НА ЭКРАН ОПИСАНИЯ ПРИ КЛИКЕ НА КАРТОЧКУ
    def on_movie_card_clicked(kp_id):
        print(f"[ИНТЕГРАЦИЯ СИГНАЛОВ]: Клик по фильму ID {kp_id}. Запрос к API...")
        data = kp_backend.get_movie_data(kp_id)
        
        # Наполняем экран описания реальными данными
        window.details_page.set_movie_context(
            kp_id=kp_id,
            title=data["title"],
            year=data["year"],
            description="Культурное наследие фонда общественного достояния. Документальные архивы и некоммерческий кинематограф.",
            cover_path=data["cover_path"]
        )
        # Переключаем стопку окон на индекс 1 (Экран деталей)
        window.screen_stack.setCurrentIndex(1)

    # 2. СЛОТ ПЕРЕХОДА В ПЛЕЕР
    def on_start_streaming(kp_id):
        print(f"[ИНТЕГРАЦИЯ СИГНАЛОВ]: Старт P2P потока для ID {kp_id}. Переход в плеер.")
        window.screen_stack.setCurrentIndex(2) # Индекс 2: Видеоплеер

    # 3. СЛОТ ВОЗВРАТА ИЗ ПЛЕЕРА ИЛИ ДЕТАЛЕЙ
    def on_back_to_feed():
        window.screen_stack.setCurrentIndex(0) # Индекс 0: Обратно к ленте

    # Подключаем кастомные сигналы к слотам переключения
    window.details_page.start_streaming_requested.connect(on_start_streaming)
    window.details_page.back_to_feed_requested.connect(on_back_to_feed)
    window.player_page.close_player_requested.connect(lambda secs: on_back_to_feed())

    # Генерируем тестовую сетку фильмов
    whitelist_mock_ids = [44745, 42664, 582144, 462244] * 2
    for index, kp_id in enumerate(whitelist_mock_ids):
        movie_data = kp_backend.get_movie_data(kp_id)
        card = MovieCardWidget(kp_id=kp_id, title=movie_data["title"], year=movie_data["year"], cover_path=movie_data["cover_path"])
        
        # ХАК СВЯЗКИ: Соединяем сигнал клика кнопки карточки с переходом на экран деталей
        card.play_requested.connect(on_movie_card_clicked)
        
        feed_widget.add_card_to_grid(card, index)
        
    layout = QVBoxLayout(window.feed_page_placeholder)
    layout.setContentsMargins(0, 0, 0, 0)
    layout.addWidget(feed_widget)
    
    window.show()
    sys.exit(app.exec())

if __name__ == "__main__":
    run_integrated_ui_test()
