"""
Главный тестовый модуль запуска Amagi-Player.
Оркестрирует инициализацию графического интерфейса PyQt6, асинхронного P2P-ядра
и связывает сигналы виджетов с бэкенд-сервисами без блокировки UI.
"""

import sys
from PyQt6.QtWidgets import QApplication, QWidget
from ui.main_window import MainWindow
from ui.widgets.feed_widget import MovieFeedWidget
from ui.widgets.details_widget import MovieDetailsWidget
from ui.widgets.player_widget import MoviePlayerWidget
from services.torrent_service import TorrentService

# Тестовая легальная magnet-ссылка (открытый мультфильм Blender Foundation - Big Buck Bunny)
# Используется как временная замена базы данных для проверки стриминга вживую
TEST_MAGNET = "magnet:?xt=urn:btih:dd8255ecdc7ca55fb0bbf81323d87062db1f6d1c&dn=Big+Buck+Bunny&tr=udp%3A%2F%2Ftracker.leechers-paradise.org%3A6969"

class AmagiController:
    """
    Архитектурный контроллер приложения.
    Отвечает за связывание изолированных слоев UI и бизнес-логики (P2P-стриминга).
    """
    def __init__(self):
        # 1. Инициализируем главное графическое окно
        self.window = MainWindow()
        
        # 2. Создаем экземпляры ваших кастомных виджетов
        self.feed_widget = MovieFeedWidget(self.window)
        self.details_widget = MovieDetailsWidget(self.window)
        self.player_widget = MoviePlayerWidget(self.window)
        
        # 3. Интегрируем виджеты в StackedWidget главного окна вместо заглушек
        # Удаляем пустые плейсхолдеры и ставим реальные экраны
        self.window.screen_stack.removeWidget(self.window.feed_page_placeholder)
        self.window.screen_stack.addWidget(self.feed_widget)
        self.window.screen_stack.addWidget(self.details_widget)
        self.window.screen_stack.addWidget(self.player_widget)
        
        # Устанавливаем стартовый экран — Ленту фильмов
        self.window.screen_stack.setCurrentWidget(self.feed_widget)

        # 4. Инициализируем P2P-сервис управления торрентом
        self.torrent_service = TorrentService()

        # 5. Запускаем коммутацию сигналов и слотов
        self._connect_signals()
        
        # Искусственно наполняем ленту одной тестовой карточкой для проверки клика
        # В будущем этот блок будет автоматизирован через циклы базы данных
        self._setup_test_data()

    def _connect_signals(self):
        """Регистрирует межкомпонентные связи и реакцию на действия пользователя."""
        
        # Навигация: Клик на кнопку «Назад» на экране описания возвращает нас к ленте
        self.details_widget.back_to_feed_requested.connect(
            lambda: self.window.screen_stack.setCurrentWidget(self.feed_widget)
        )
        
        # Главное событие: Клик на монолитную кнопку «ЗАПУСТИТЬ ТРАНСЛЯЦИЮ»
        self.details_widget.start_streaming_requested.connect(self.handle_start_streaming)
        
        # Остановка: Клик на кнопку «✕ ЗАКРЫТЬ ТРАНСЛЯЦИЮ» внутри плеера
        self.player_widget.close_player_requested.connect(self.handle_stop_streaming)

    def _setup_test_data(self):
        """Временный метод ручного наполнения интерфейса до готовности слоя SQLite."""
        # Напрямую вызываем ваш метод установки контекста, имитируя клик по карточке
        # Передаем ID, Название, Год, Описание и пустую строку вместо постера
        self.details_widget.set_movie_context(
            kp_id=1, 
            title="Тестовый P2P Стриминг", 
            year="2026", 
            description="Нажмите кнопку ниже для проверки скрытого запуска qBittorrent.exe и старта асинхронной последовательной буферизации видеопотока.",
            cover_path=""
        )
        # Временно переключаем стек сразу на экран описания, чтобы сократить путь до теста
        self.window.screen_stack.setCurrentWidget(self.details_widget)

    def start(self):
        """Безопасно разворачивает фоновые движки и выводит окно на экран."""
        print("[СИСТЕМНЫЙ КОНТРОЛЛЕР]: Запуск P2P движка...")
        
        # Вызываем наш метод проверки системы на краши и скрытого запуска exe
        if self.torrent_service.start_engine():
            print("[СИСТЕМНЫЙ КОНТРОЛЛЕР]: P2P движок успешно запущен в фоне.")
            self.window.show()
        else:
            print("[КРИТИЧЕСКАЯ ОШИБКА]: Ошибка инициализации P2P-модуля. Запуск отменен.")
            sys.exit(1)

    def handle_start_streaming(self, kp_id: int):
        """Обработчик асинхронной инициализации стриминга."""
        print(f"[БИЗНЕС-ЛОГИКА]: Получен запрос на запуск трансляции для ID {kp_id}")
        
        # Переключаем экран интерфейса на ваш OLED-плеер с полосой загрузки
        self.window.screen_stack.setCurrentWidget(self.player_widget)
        
        # Передаем тестовый magnet в сервис и связываем сигналы асинхронного потока 
        # НАПРЯМУЮ с вашим методом обновления прогресс-бара set_buffering_progress
        self.torrent_service.start_streaming(
            magnet_link=TEST_MAGNET,
            progress_callback=self.player_widget.set_buffering_progress, # Ваша заглушка в UI!
            stats_callback=self.handle_torrent_stats
        )

    def handle_torrent_stats(self, speed: float, peers: int):
        """Принимает из фонового потока скорость и пиры для отладки в консоли."""
        # Пока в UI плеера нет текстовых полей под скорость, выводим данные в инженерную консоль
        if speed > 0 or peers > 0:
            print(f"[P2P МОНИТОРИНГ]: Скорость загрузки: {speed:.2f} КБ/с | Активных пиров: {peers}")

    def handle_stop_streaming(self, current_seconds: int):
        """Останавливает загрузку и возвращает пользователя на главный экран."""
        print(f"[БИЗНЕС-ЛОГИКА]: Трансляция остановлена пользователем на {current_seconds} секунде.")
        
        # Даем команду сервису отключить фоновый поток слежки
        self.torrent_service.stop_streaming()
        
        # Возвращаем интерфейс обратно на экран описания фильма
        self.window.screen_stack.setCurrentWidget(self.details_widget)


def main():
    # Стандартная инициализация приложения PyQt6
    app = QApplication(sys.argv)
    
    # Создаем наш контролирующий бэкенд-центр
    controller = AmagiController()
    
    # Запускаем логику проверки процессов и открываем окно
    controller.start()
    
    # При закрытии главного окна Amagi-Player принудительно тушим скрытый qBittorrent.exe
    code = app.exec()
    controller.torrent_service.shutdown_engine()
    sys.exit(code)

if __name__ == "__main__":
    main()
