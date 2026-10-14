import sys
from PyQt6.QtWidgets import QApplication

# Импортируем глобальный конфиг
import config

# Импортируем готовые сервисы
from services.kp_service import KPService
from services.torrent_scraper import TorrentScraper
from services.torrent_service import TorrentService

# Импортируем компоненты интерфейса
from ui.main_window import MainWindow
from ui.widgets.card_widget import MovieCardWidget

# ==============================================================================
# ВРЕМЕННЫЙ ВАЙТЛИСТ (Пока нет SQLite)
# Сюда внесены ID популярных фильмов Общественного достояния для теста вайтлиста
# ==============================================================================
MOCK_WHITELIST_IDS = [
    8111,   # Ночь живых мертвецов (1968) - Night of the Living Dead
    429033, # Путешествие на Луну (1902) - Le voyage dans la lune
    41520,  # Генерал (1926) - The General (Бастер Китон)
    229415, # Малыш (1921) - The Kid (Чарли Чаплин)
]

class AmagiController:
    """
    Главный управляющий диспетчер автоматического P2P-плеера.
    Связывает сетевой поиск, авто-парсер торрентов и движок стриминга.
    """
    def __init__(self):
        # Инициализируем бэкенд-сервисы
        self.kp_service = KPService()
        self.torrent_scraper = TorrentScraper()
        self.torrent_service = TorrentService()
        
        # Словарь для оперативного сохранения метаданных найденных фильмов
        self._current_search_results = {}
        
        # Инициализируем главное графическое окно
        self.window = MainWindow()
        
        # Запускаем скрытый фоновый qBittorrent
        if self.torrent_service.start_engine():
            print("[КОНТРОЛЛЕР]: Скрытый фоновый P2P-движок успешно запущен.")
        else:
            print("[КОНТРОЛЛЕР]: Критическая ошибка! Не удалось развернуть P2P-движок.")

        # Соединяем сигналы интерфейса с нашей логикой
        self._connect_signals()
        
        # Показываем стартовую заглушку или пустую ленту
        print("[КОНТРОЛЛЕР]: Приложение готово. Введите название фильма в строку поиска...")

    def _connect_signals(self):
        """Связывает сигналы PyQt виджетов с методами управления."""
        # 1. Сквозной поиск: запускается автоматически при вводе текста
        self.window.search_bar.textChanged.connect(self.handle_live_search)
        
        # 2. Навигация: кнопка "Назад" на экране детального описания
        self.window.details_page.back_to_feed_requested.connect(
            lambda: self.window.screen_stack.setCurrentIndex(0)
        )
        
        # 3. Кнопка запуска: автоматический поиск торрента и старт стриминга
        self.window.details_page.start_streaming_requested.connect(self.handle_auto_streaming)
        
        # 4. Видеоплеер: кнопка "Закрыть трансляцию"
        self.window.player_page.close_player_requested.connect(self.handle_stop_streaming)

    def handle_live_search(self, text: str):
        """
        Слот живого поиска. Срабатывает при каждом вводе символа.
        Обращается к API Кинопоиска и динамически перерисовывает ленту карточек.
        """
        keyword = text.strip()
        
        # Очищаем текущую сетку на экране ленты
        self.window.feed_page.clear_grid()
        self._current_search_results.clear()

        # Если поисковая строка пустая — оставляем экран чистым
        if not keyword:
            return

        print(f"[КОНТРОЛЛЕР]: Запрос к API Кинопоиска по ключевому слову: '{keyword}'...")
        # Дергаем наш обновленный метод сетевого поиска
        found_films = self.kp_service.search_movies(keyword)
        
        visible_index = 0
        for film in found_films:
            kp_id = film["kp_id"]

            # --- ПРОВЕРКА ВАЙТЛИСТА (КУЛЬТУРНОГО ФОНДА) ---
            # Если строгий режим включен, а фильма нет во временном списке разрешенных — игнорируем его
            if config.USE_WHITELIST and kp_id not in MOCK_WHITELIST_IDS:
                continue

            # Сохраняем во внутренний буфер, чтобы не дергать API повторно при клике
            self._current_search_results[kp_id] = film

            # Создаем динамический виджет карточки
            # Мы передаем poster_url из результатов поиска, но внутри виджет может взять локальный кэш
            card = MovieCardWidget(
                kp_id=kp_id,
                title=film["title"],
                year=film["year"],
                cover_path="", # Передаем пустоту, так как get_movie_data скачает постер на следующем шаге
                parent=self.window.feed_page.grid_container
            )
            
            # Подгружаем кэшированную или скачанную обложку для этой карточки
            meta = self.kp_service.get_movie_data(kp_id)
            if meta["cover_path"]:
                card.cover_label.setPixmap(card.QPixmap(meta["cover_path"]))

            # Подключаем клик по карточке к открытию экрана деталей
            card.play_requested.connect(self.handle_open_details)
            
            # Рендерим карточку в сетку
            self.window.feed_page.add_card_to_grid(card, visible_index)
            visible_index += 1

    def handle_open_details(self, kp_id: int):
        """Запрашивает полные метаданные фильма и переключает стек на экран описания."""
        print(f"[КОНТРОЛЛЕР]: Загрузка карточки описания для ID {kp_id}...")
        meta = self.kp_service.get_movie_data(kp_id)
        
        # Передаем контекст на холст деталей
        self.window.details_page.set_movie_context(
            kp_id=kp_id,
            title=meta["title"],
            year=meta["year"],
            description=meta["description"],
            cover_path=meta["cover_path"]
        )
        
        # Переключаем QStackedWidget на экран деталей (Индекс 1)
        self.window.screen_stack.setCurrentIndex(1)

    def handle_auto_streaming(self, kp_id: int):
        """
        СЕРДЦЕ АВТОМАТА: Берет текстовые данные фильма, сама ищет торрент в сети,
        генерирует magnet-ссылку и скармливает её в фоновый qBittorrent.
        """
        meta = self.kp_service.get_movie_data(kp_id)
        title_ru = meta["title"]
        year = meta["year"]
        
        # Пытаемся достать оригинальное название из буфера поиска (для Internet Archive)
        cached_film = self._current_search_results.get(kp_id, {})
        title_orig = cached_film.get("title", title_ru) 

        # Включаем OLED-экран видеоплеера (Индекс 2)
        self.window.screen_stack.setCurrentIndex(2)
        self.window.player_page.loader_label.setText("АВТОМАТИЧЕСКИЙ ПОИСК P2P РАЗДАЧИ В СЕТИ...")
        self.window.player_page.p2p_progress.setValue(10)

        print(f"[КОНТРОЛЛЕР АВТОМАТ]: Поиск торрент-потока для '{title_ru}' ({year})...")
        
        # ЗАПУСКАЕМ АВТОПОИСК ТОРРЕНТА (Через выбранный в config провайдер)
        torrent_source = self.torrent_scraper.find_best_magnet(
            title_ru=title_ru, 
            title_orig=title_orig, 
            year=year
        )
        
        if not torrent_source:
            print("[КОНТРОЛЛЕР АВТОМАТ]: Раздач не найдено. Стриминг невозможен.")
            self.window.player_page.loader_label.setText("ОШИБКА: СТАТИСТИКА ПОТОКА НЕ НАЙДЕНА В СЕТИ")
            return

        # Передаем найденный торрент (magnet или url) в qBittorrent на последовательное скачивание
        self.window.player_page.loader_label.setText("ПОСЛЕДОВАТЕЛЬНАЯ БУФЕРИЗАЦИЯ P2P ПОТОКА...")
        self.torrent_service.start_streaming(
            magnet_link=torrent_source,
            progress_callback=self.window.player_page.set_buffering_progress,
            stats_callback=self._on_torrent_stats_updated
        )

    def handle_stop_streaming(self, current_seconds: int):
        """Останавливает скачивание торрента и возвращает пользователя на экран деталей."""
        print(f"[КОНТРОЛЛЕР]: Трансляция закрыта. Остановка P2P сессии.")
        self.torrent_service.stop_streaming()
        
        self.window.screen_stack.setCurrentIndex(1)
        
        # Показываем красивый Liquid Glass остров истории (в ОЗУ)
        kp_id = self.window.details_page._current_kp_id
        meta = self.kp_service.get_movie_data(kp_id)
        self.window.show_resume_bar(movie_id=kp_id, movie_title=meta["title"])

    def _on_torrent_stats_updated(self, speed_kb: float, peers: int):
        """Принимает из фонового потока скорость и количество пиров."""
        # Для отладки пишем в консоль реальную скорость P2P-стриминга
        if speed_kb > 0:
            print(f"[P2P СТАТСЫ]: Скорость: {speed_kb:.2f} КБ/с, Пиры: {peers}")

    def shutdown(self):
        """Гарантирует чистое уничтожение скрытого qBittorrent при выходе."""
        print("[КОНТРОЛЛЕР]: Закрытие приложения. Уничтожение фонового qBittorrent...")
        self.torrent_service.shutdown_engine()

# ==============================================================================
# ЗАПУСК ПРИЛОЖЕНИЯ
# ==============================================================================
if __name__ == "__main__":
    app = QApplication(sys.argv)
    controller = AmagiController()
    controller.window.show()
    
    # Привязываем уничтожение зомби-процессов к закрытию окна
    app.aboutToQuit.connect(controller.shutdown)
    sys.exit(app.exec())
