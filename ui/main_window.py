"""
Модуль главного графического окна Amagi-Player.
Реализует премиальную дизайн-систему OLED Minimalism с вертикальным 
двухуровневым островом истории Liquid Glass 2.0.
"""
# СТРОГО ПО ТЗ: Импортируем все три необходимых виджета
from ui.widgets.feed_widget import MovieFeedWidget
from ui.widgets.details_widget import MovieDetailsWidget
from ui.widgets.player_widget import MoviePlayerWidget

from PyQt6.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, 
    QStackedWidget, QPushButton, QLabel, QFrame, QLineEdit
)
from PyQt6.QtCore import pyqtSignal, QPoint, Qt  # Добавлен Qt для выравнивания текста
import os
import config

class MainWindow(QMainWindow):
    """
    Главное графическое окно приложения Amagi-Player.
    """
    theme_toggle_requested = pyqtSignal()
    settings_opened = pyqtSignal()
    resume_movie_requested = pyqtSignal(int)

    def __init__(self):
        super().__init__()
        self.setWindowTitle("Amagi-Player")
        self.resize(1150, 820)
        self._current_resume_id = None
        
        self._init_ui_core()
        self._load_stylesheet()

    def _init_ui_core(self):
        """Инициализирует структуру слоев интерфейса."""
        central_widget = QWidget(self)
        self.setCentralWidget(central_widget)
        
        base_layout = QVBoxLayout(central_widget)
        base_layout.setContentsMargins(0, 0, 0, 0)
        base_layout.setSpacing(0)

        # 1. МОНОЛИТНАЯ ВЕРХНЯЯ ШАПКА (HEADER BAR)
        self.header_bar = QWidget(central_widget)
        self.header_bar.setObjectName("headerBar")
        self.header_bar.setFixedHeight(75)
        
        header_layout = QHBoxLayout(self.header_bar)
        header_layout.setContentsMargins(40, 0, 40, 0)
        
        # Пафосный разреженный логотип AMAGI
        logo_label = QLabel("AMAGI", self.header_bar)
        logo_label.setObjectName("logoLabel")
        header_layout.addWidget(logo_label)
        header_layout.addSpacing(60)
        
        # Поисковая строка в дорогой белой рамке
        self.search_bar = QLineEdit(self.header_bar)
        self.search_bar.setObjectName("searchBar")
        self.search_bar.setPlaceholderText("ПОИСК ПО КУЛЬТУРНОМУ ФОНДУ...")
        self.search_bar.setFixedWidth(400)
        header_layout.addWidget(self.search_bar)
        
        header_layout.addStretch()
        base_layout.addWidget(self.header_bar)

        # 2. РАБОЧАЯ ЗОНА КОНТЕНТА
        content_wrapper = QWidget(central_widget)
        content_layout = QVBoxLayout(content_wrapper)
        content_layout.setContentsMargins(40, 35, 40, 25)
        content_layout.setSpacing(20)

        # Стек экранов
        self.screen_stack = QStackedWidget(content_wrapper)
        
        # ЧТО ДОПИСАНО: Инициализируем полноценные страницы согласно run_ui_test.py
        self.feed_page = MovieFeedWidget(content_wrapper)
        self.details_page = MovieDetailsWidget(content_wrapper)
        self.player_page = MoviePlayerWidget(content_wrapper)
        self.settings_page_placeholder = QWidget() # Оставляем заглушку настроек
        
        # Добавляем страницы в стек управления (Порядок индексов: 0, 1, 2, 3)
        self.screen_stack.addWidget(self.feed_page)                # Индекс 0
        self.screen_stack.addWidget(self.details_page)             # Индекс 1
        self.screen_stack.addWidget(self.player_page)              # Индекс 2
        self.screen_stack.addWidget(self.settings_page_placeholder) # Индекс 3
        
        content_layout.addWidget(self.screen_stack)

        # Нижняя системная панель кнопок
        bottom_bar = QWidget(content_wrapper)
        bottom_layout = QHBoxLayout(bottom_bar)
        bottom_layout.setContentsMargins(0, 0, 0, 0)
        bottom_layout.addStretch()
        
        self.theme_btn = QPushButton("Сменить тему", bottom_bar)
        self.theme_btn.setObjectName("sysButton")
        bottom_layout.addWidget(self.theme_btn)
        
        self.settings_btn = QPushButton("Настройки", bottom_bar)
        self.settings_btn.setObjectName("sysButton")
        self.settings_btn.clicked.connect(self._on_settings_clicked)
        bottom_layout.addWidget(self.settings_btn)
        
        content_layout.addWidget(bottom_bar)
        base_layout.addWidget(content_wrapper)

        # 3. ПАРЯЩИЙ ОСТРОВ ИСТОРИИ (ВЕРТИКАЛЬНЫЙ LIQUID GLASS 2.0)
        self.resume_island = QFrame(central_widget)
        self.resume_island.setObjectName("continueIsland")
        self.resume_island.setFixedSize(420, 96)
        
        island_layout = QVBoxLayout(self.resume_island)
        island_layout.setContentsMargins(20, 15, 20, 15)
        island_layout.setSpacing(10)
        
        self.resume_label = QLabel("НАЗВАНИЕ ФИЛЬМА...", self.resume_island)
        self.resume_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.resume_label.setWordWrap(True)
        island_layout.addWidget(self.resume_label)
        
        self.resume_action_btn = QPushButton("Продолжить просмотр", self.resume_island)
        self.resume_action_btn.setObjectName("islandActionButton")
        self.resume_action_btn.setFixedHeight(32)
        self.resume_action_btn.clicked.connect(self._on_resume_action_triggered)
        island_layout.addWidget(self.resume_action_btn)
        
        # ... (ваш код инициализации island_layout)
        self.resume_action_btn.clicked.connect(self._on_resume_action_triggered)
        island_layout.addWidget(self.resume_action_btn)
        
        # ИСПРАВЛЕНИЕ: Передаем родителем сам остров, но НЕ добавляем в layout,
        # чтобы move() работал корректно относительно границ плашки
        self.resume_close_btn = QPushButton("×", self.resume_island) 
        self.resume_close_btn.setObjectName("closeIslandButton")
        self.resume_close_btn.setFixedSize(20, 20)
        self.resume_close_btn.move(395, 5) # Теперь позиционирование сработает жестко
        self.resume_close_btn.clicked.connect(self.resume_island.hide)
        
        self.resume_island.hide()

        
        self.resume_island.hide()

    def resizeEvent(self, event):
        """Пересчитывает центр экрана для нового вертикального острова."""
        super().resizeEvent(event)
        if self.resume_island.isVisible():
            self._reposition_resume_island()

    def _reposition_resume_island(self):
        """Центрирует плашку по горизонтали и вешает её над нижними кнопками."""
        x = (self.width() - self.resume_island.width()) // 2
        y = self.height() - self.resume_island.height() - 95
        self.resume_island.move(QPoint(x, y))

    def _load_stylesheet(self):
        qss_path = os.path.join(config.BASE_DIR, "ui", "styles.qss")
        if os.path.exists(qss_path):
            with open(qss_path, "r", encoding="utf-8") as f:
                self.setStyleSheet(f.read())

    def _on_settings_clicked(self):
        self.screen_stack.setCurrentIndex(3)  # Индекс изменен на 3, так как 1 и 2 заняты деталями и плеером
        self.settings_opened.emit()

    def _on_resume_action_triggered(self):
        if self._current_resume_id is not None:
            self.resume_movie_requested.emit(self._current_resume_id)

    def show_resume_bar(self, movie_id: int, movie_title: str):
        """Отображает обновленный двухуровневый остров."""
        self._current_resume_id = movie_id
        self.resume_label.setText(f"<b>{movie_title.upper()}</b>")
        self.resume_island.show()
        self._reposition_resume_island()
