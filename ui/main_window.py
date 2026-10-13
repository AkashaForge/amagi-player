from PyQt6.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, 
    QStackedWidget, QPushButton, QLabel, QFrame, QLineEdit
)
from PyQt6.QtCore import pyqtSignal, QPoint
import os
import config

class MainWindow(QMainWindow):
    theme_toggle_requested = pyqtSignal()
    settings_opened = pyqtSignal()
    resume_movie_requested = pyqtSignal(int)

    def __init__(self):
        super().__init__()
        self.setWindowTitle("Amagi-Player")
        self.resize(1150, 820) # Оптимальный размер для дорогого визуала
        self._current_resume_id = None
        
        self._init_ui_core()
        self._load_stylesheet()

    def _init_ui_core(self):
        central_widget = QWidget(self)
        self.setCentralWidget(central_widget)
        
        base_layout = QVBoxLayout(central_widget)
        base_layout.setContentsMargins(0, 0, 0, 0)
        base_layout.setSpacing(0)

        # 1. СТЕКЛЯННАЯ ВЕРХНЯЯ ПАНЕЛЬ (HEADER BAR)
        self.header_bar = QWidget(central_widget)
        self.header_bar.setObjectName("headerBar")
        self.header_bar.setFixedHeight(75)
        
        header_layout = QHBoxLayout(self.header_bar)
        header_layout.setContentsMargins(40, 0, 40, 0)
        
        # Логотип AMAGI (Стильный, разреженный шрифт Кинопоиска)
        logo_label = QLabel("AMAGI", self.header_bar)
        logo_label.setStyleSheet("""
            color: #FFFFFF; 
            font-size: 24px; 
            font-weight: 900; 
            letter-spacing: 5px;
        """)
        header_layout.addWidget(logo_label)
        header_layout.addSpacing(50)
        
        # Премиальная строка поиска
        self.search_bar = QLineEdit(self.header_bar)
        self.search_bar.setObjectName("searchBar")
        self.search_bar.setPlaceholderText("Поиск фильмов по культурному фонду...")
        self.search_bar.setFixedWidth(420)
        header_layout.addWidget(self.search_bar)
        
        header_layout.addStretch()
        base_layout.addWidget(self.header_bar)

        # 2. ОСНОВНАЯ ЗОНА КОНТЕНТА
        content_wrapper = QWidget(central_widget)
        content_layout = QVBoxLayout(content_wrapper)
        content_layout.setContentsMargins(40, 30, 40, 25) # Просторные отступы
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

        # 3. ПАРЯЩИЙ ОСТРОВ «ПРОДОЛЖИТЬ ПРОСМОТР» (FLOATING ISLAND)
        self.resume_island = QFrame(central_widget)
        self.resume_island.setObjectName("continueIsland")
        self.resume_island.setFixedSize(560, 56)
        
        island_layout = QHBoxLayout(self.resume_island)
        island_layout.setContentsMargins(25, 0, 15, 0)
        
        self.resume_label = QLabel("Продолжить просмотр: ...", self.resume_island)
        island_layout.addWidget(self.resume_label)
        island_layout.addStretch()
        
        self.resume_action_btn = QPushButton("Смотреть", self.resume_island)
        self.resume_action_btn.setObjectName("actionButton")
        self.resume_action_btn.setFixedHeight(34)
        self.resume_action_btn.clicked.connect(self._on_resume_action_triggered)
        island_layout.addWidget(self.resume_action_btn)
        
        self.resume_close_btn = QPushButton("×", self.resume_island)
        self.resume_close_btn.setObjectName("closeIslandButton")
        self.resume_close_btn.setFixedSize(24, 24)
        self.resume_close_btn.clicked.connect(self.resume_island.hide)
        island_layout.addWidget(self.resume_close_btn)
        
        self.resume_island.hide()

    def resizeEvent(self, event):
        super().resizeEvent(event)
        if self.resume_island.isVisible():
            self._reposition_resume_island()

    def _reposition_resume_island(self):
        x = (self.width() - self.resume_island.width()) // 2
        y = self.height() - self.resume_island.height() - 90 # Чуть приподнимем над кнопками
        self.resume_island.move(QPoint(x, y))

    def _load_stylesheet(self):
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
        self._current_resume_id = movie_id
        self.resume_label.setText(f"Продолжить: <b>{movie_title}</b>")
        self.resume_island.show()
        self._reposition_resume_island()
