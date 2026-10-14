import sys
from PyQt6.QtWidgets import QApplication

# Импортируем конфигурацию и сервисы
import config
from services.kp_service import KPService
from services.torrent_service import TorrentService

# Импортируем компоненты интерфейса
from ui.main_window import MainWindow
from ui.widgets.card_widget import MovieCardWidget

# ==============================================================================
# ВРЕМЕННАЯ ТЕСТОВАЯ БАЗА ДАННЫХ (Пока не реализован database слой)
# Здесь используются реальные ID популярных фильмов на Кинопоиске для проверки API
# ==============================================================================
TEST_MOVIES_DB = [
    {
        "kp_id": 326, 
        "title": "Побег из Шоушенка", 
        "magnet": "magnet:?xt=urn:btih:demo_hash_shawshank&dn=Shawshank",
        "is_whitelisted": True
    },
    {
        "kp_id": 435, 
        "title": "Зеленая миля", 
        "magnet": "magnet:?xt=urn:btih:demo_hash_green_mile&dn=GreenMile",
        "is_whitelisted": True
    },
    {
        "kp_id": 342, 
        "title": "Криминальное чтиво", 
        "magnet": "magnet:?xt=urn:btih:demo_hash_pulp_fiction&dn=PulpFiction",
        "is_whitelisted": False  # Этот фильм НЕ в вайтлисте
    },
    {
        "kp_id": 464963, 
        "title": "Интерстеллар", 
        "magnet": "magnet:?xt=urn:btih:demo_hash_interstellar&dn=Interstellar",
        "is_whitelisted": False  # Этот фильм НЕ в вайтлисте
    }
]

class AmagiController:
    """
    Главный диспетчер (Контроллер) приложения.
    Связывает сигналы интерфейса с бизнес-логикой бэкенда.
    """
    def __init__(self):
        # Инициализируем сервисы
        self.kp_service = KPService()
        self.torrent_service = TorrentService()
        
        # Инициализируем главное окно
        self.window = MainWindow()
        
        # Запускаем движок торрента в фоновом режиме
        if self.torrent_service.start_engine():
            print("[КОНТРОЛЛЕР]: P2P Движок qBittorrent успешно запущен.")
        else:
            print("[КОНТРОЛЛЕР]: Предупреждение! Не удалось запустить движок торрента.")

        # Подключаем сигналы интерфейса к слотам контроллера
        self._connect_signals()
        
        # Первичная отрисовка ленты при запуске приложения
        self.refresh_movie_feed()

    def _connect_signals(self):
        """Связывает сигналы элементов UI с методами контроллера."""
        # 1. Поиск: при любом изменении текста вызываем фильтрацию
        self.window.search_bar.textChanged.connect(self.refresh_movie_feed)
        
        # 2. Навигация: возврат из деталей обратно в ленту
        self.window.details_page.back_to_feed_requested.connect(
            lambda: self.window.screen_stack.setCurrentIndex(0)
        )
        
        # 3. Стриминг: запуск трансляции с экрана деталей
        self.window.details_page.start_streaming_requested.connect(self.handle_start_streaming)
        
        # 4. Плеер: закрытие трансляции и возврат на экран деталей
        self.window.player_page.close_player_requested.connect(self.handle_stop_streaming)

    def refresh_movie_feed(self):
        """
        Основная функция фильтрации и отрисовки ленты.
        Отрабатывает логику: Вайтлист -> Поисковый запрос -> Отрендерить карточки.
        """
        # Очищаем текущую сетку в UI
        self.window.feed_page.clear_grid()
        
        search_text = self.window.search_bar.text().strip().lower()
        visible_index = 0

        for movie in TEST_MOVIES_DB:
            # --- Шаг 1: Фильтрация по Вайтлисту ---
            # Если строгий режим включен, а фильма нет в вайтлисте — пропускаем его
            if config.USE_WHITELIST and not movie["is_whitelisted"]:
                continue
                
            # --- Шаг 2: Фильтрация по Поисковому Запросу ---
            # Если в поиске что-то введено, и оно не совпадает с названием — пропускаем
            if search_text and search_text not in movie["title"].lower():
                continue

            # --- Шаг 3: Получение данных и создание карточки ---
            # Запрашиваем метаданные и путь к обложке (сработает умный кэш)
            meta = self.kp_service.get_movie_data(movie["kp_id"])
            
            # Создаем виджет карточки
            card = MovieCardWidget(
                kp_id=movie["kp_id"],
                title=meta["title"],
                year=meta["year"],
                cover_path=meta["cover_path"],
                parent=self.window.feed_page.grid_container
            )
            
            # Связываем клик по созданной карточке с открытием экрана деталей
            card.play_requested.connect(self.handle_open_details)
            
            # Добавляем карточку в адаптивную сетку ленты
            self.window.feed_page.add_card_to_grid(card, visible_index)
            visible_index += 1

    def handle_open_details(self, kp_id: int):
        """Переключает стек на экран детальной информации о выбранном фильме."""
        # Находим фильм в нашей тестовой базе данных
        movie = next((m for m in TEST_MOVIES_DB if m["kp_id"] == kp_id), None)
        if not movie:
            return

        # Получаем актуальные данные (из кэша или API)
        meta = self.kp_service.get_movie_data(kp_id)
        
        # Заполняем холст экрана деталей данными
        self.window.details_page.set_movie_context(
            kp_id=kp_id,
            title=meta["title"],
            year=meta["year"],
            description=meta["description"],
            cover_path=meta["cover_path"]
        )
        
        # Переключаем экран stacked_widget на индекс 1 (MovieDetailsWidget)
        self.window.screen_stack.setCurrentIndex(1)

    def handle_start_streaming(self, kp_id: int):
        """Инициализирует P2P-поток и переключает интерфейс в режим плеера."""
        movie = next((m for m in TEST_MOVIES_DB if m["kp_id"] == kp_id), None)
        if not movie:
            return

        # Переключаем стек экранов на индекс 2 (MoviePlayerWidget)
        self.window.screen_stack.setCurrentIndex(2)
        
        # Запускаем стриминг торрента через magnet-ссылку.
        # Передаем колбэки для обновления прогресса и статистики прямо в UI плеера
        self.torrent_service.start_streaming(
            magnet_link=movie["magnet"],
            progress_callback=self.window.player_page.set_buffering_progress,
            stats_callback=self._on_torrent_stats_updated
        )

    def handle_stop_streaming(self, current_seconds: int):
        """Останавливает P2P-поток, закрывает плеер и показывает плашку сохранения истории."""
        print(f"[КОНТРОЛЛЕР]: Просмотр остановлен на {current_seconds} сек. Запись в историю.")
        
        # Находим текущий запущенный фильм, чтобы узнать его название для плашки
        kp_id = self.window.details_page._current_kp_id
        movie = next((m for m in TEST_MOVIES_DB if m["kp_id"] == kp_id), None)
        
        # Останавливаем мониторинг торрента
        self.torrent_service.stop_streaming()
        
        # Возвращаем пользователя на экран описания фильма (индекс 1)
        self.window.screen_stack.setCurrentIndex(1)
        
        # Если фильм был найден, отображаем всплывающий Liquid Glass остров истории
        if movie:
            self.window.show_resume_bar(movie_id=movie["kp_id"], movie_title=movie["title"])

    def _on_torrent_stats_updated(self, speed_kb: float, peers: int):
        """Внутренний слот для логирования расширенной статистики торрента."""
        # Здесь в будущем можно выводить скорость и пиры на панель плеера
        pass

    def cleanup(self):
        """Корректное закрытие всех фоновых процессов при выходе."""
        print("[КОНТРОЛЛЕР]: Завершение работы. Корректная остановка торрент-движка...")
        self.torrent_service.shutdown_engine()


# ==============================================================================
# ТОЧКА ВХОДА В ПРОГРАММУ
# ==============================================================================
if __name__ == "__main__":
    app = QApplication(sys.argv)
    
    # Инициализируем контроллер архитектуры
    controller = AmagiController()
    
    # Показываем главное окно приложения
    controller.window.show()
    
    # Гарантируем, что при закрытии окна qBittorrent не останется висеть в памяти
    app.aboutToQuit.connect(controller.cleanup)
    
    sys.exit(app.exec())
