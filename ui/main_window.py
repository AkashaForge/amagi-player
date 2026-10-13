"""
Модуль главного графического окна Amagi-Player.
Реализует премиальную дизайн-систему OLED Minimalism с эффектами Liquid Glass,
парящей строкой поиска в белой рамке и пафосными разреженными шрифтами.
"""

from PyQt6.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, 
    QStackedWidget, QPushButton, QLabel, QFrame, QLineEdit
)
from PyQt6.QtCore import pyqtSignal, QPoint
import os
import config

class MainWindow(QMainWindow):
    """
    Главное графическое окно приложения Amagi-Player в ультра-минималистичном стиле.
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
        """Иннициализирует монолитную структуру слоев интерфейса."""
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
        self.feed_page_placeholder = QWidget()
        self.settings_page_placeholder = QWidget()
        self.screen_stack.addWidget(self.feed_page_placeholder)
        self.screen_stack.addWidget(self.settings_page_placeholder)
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

        # 3. ПАРЯЩИЙ ОСТРОВ ИСТОРИИ (ЭФФЕКТ LIQUID GLASS)
        self.resume_island = QFrame(central_widget)
        self.resume_island.setObjectName("continueIsland")
        self.resume_island.setFixedSize(600, 52) # Более вытянутая, строгая плашка
        
        island_layout = QHBoxLayout(self.resume_island)
        island_layout.setContentsMargins(25, 0, 15, 0)
        
        # Текст на плашке (будет автоматически переведен в верхний регистр бэкендом)
        self.resume_label = QLabel("ПРОДОЛЖИТЬ ПРОСМОТР: ...", self.resume_island)
        island_layout.addWidget(self.resume_label)
        
        island_layout.addStretch()
        
        # Монолитная белая кнопка действия
        self.resume_action_btn = QPushButton("Смотреть", self.resume_island)
        self.resume_action_btn.setObjectName("actionButton")
        self.resume_action_btn.setFixedHeight(30)
        self.resume_action_btn.clicked.connect(self._on_resume_action_triggered)
        island_layout.addWidget(self.resume_action_btn)
        
        # Минималистичный крестик закрытия
        self.resume_close_btn = QPushButton("×", self.resume_island)
        self.resume_close_btn.setObjectName("closeIslandButton")
        self.resume_close_btn.setFixedSize(24, 24)
        self.resume_close_btn.clicked.connect(self.resume_island.hide)
        island_layout.addWidget(self.resume_close_btn)
        
        self.resume_island.hide()

    def resizeEvent(self, event):
        """Гарантирует идеальное центрирование острова жидкого стекла при изменении окна."""
        super().resizeEvent(event)
        if self.resume_island.isVisible():
            self._reposition_resume_island()

    def _reposition_resume_island(self):
        """Инженерный расчет координат парящего острова над нижними кнопками."""
        x = (self.width() - self.resume_island.width()) // 2
        y = self.height() - self.resume_island.height() - 95
        self.resume_island.move(QPoint(x, y))

    def _load_stylesheet(self):
        """Считывание QSS-модуля дизайна."""
        qss_path = os.path.join(config.BASE_DIR, "ui", "styles.qss")
        if os.path.exists(qss_path):
            with open(qss_path, "r", encoding="utf-8") as f:
                self.setStyleSheet(f.read())

    def _on_settings_clicked(self):
        self.screen_stack.setCurrentIndex(1)
        self.settings_opened.emit()

    def _on_resume_action_triggered(self):
        if self._current_resume_id is not None:
            self.resume_movie_requested.emit(self._current_resume_id)

    def show_resume_bar(self, movie_id: int, movie_title: str):
        """Публичный интерфейс вызова плашки из бэкенда."""
        self._current_resume_id = movie_id
        # Переводим название в верхний регистр для сохранения пафосного стиля
        self.resume_label.setText(f"ПРОДОЛЖИТЬ: <b>{movie_title.upper()}</b>")
        self.resume_island.show()
        self._reposition_resume_island()
