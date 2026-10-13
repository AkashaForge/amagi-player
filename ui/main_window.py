"""
Модуль главного графического окна Amagi-Player.
Реализует дизайн-систему Cinematic Dark, верхнюю панель навигации (Header),
парящий остров продолжения просмотра и менеджер экранов.
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
    Главное окно приложения в стиле современных стриминговых медиаплатформ.
    """
    
    theme_toggle_requested = pyqtSignal()
    settings_opened = pyqtSignal()
    resume_movie_requested = pyqtSignal(int)

    def __init__(self):
        super().__init__()
        self.setWindowTitle("Amagi-Player")
        self.resize(1100, 800)
        self._current_resume_id = None
        
        self._init_ui_core()
        self._load_stylesheet()

    def _init_ui_core(self):
        """Разворачивает структуру слоев приложения."""
        central_widget = QWidget(self)
        self.setCentralWidget(central_widget)
        
        base_layout = QVBoxLayout(central_widget)
        base_layout.setContentsMargins(0, 0, 0, 0)
        base_layout.setSpacing(0)

        # 1. Верхняя панель (Header)
        self.header_bar = QWidget(central_widget)
        self.header_bar.setObjectName("headerBar")
        self.header_bar.setFixedHeight(70)
        
        header_layout = QHBoxLayout(self.header_bar)
        header_layout.setContentsMargins(30, 0, 30, 0)
        
        logo_label = QLabel("AMAGI", self.header_bar)
        logo_label.setStyleSheet("color: #FF6600; font-size: 22px; font-weight: 900; letter-spacing: 2px;")
        header_layout.addWidget(logo_label)
        header_layout.addSpacing(40)
        
        self.search_bar = QLineEdit(self.header_bar)
        self.search_bar.setObjectName("searchBar")
        self.search_bar.setPlaceholderText("Поиск по легальному некоммерческому фонду...")
        self.search_bar.setFixedWidth(450)
        header_layout.addWidget(self.search_bar)
        
        header_layout.addStretch()
        base_layout.addWidget(self.header_bar)

        # 2. Рабочая зона
        content_wrapper = QWidget(central_widget)
        content_layout = QVBoxLayout(content_wrapper)
        content_layout.setContentsMargins(30, 20, 30, 20)
        content_layout.setSpacing(15)

        self.screen_stack = QStackedWidget(content_wrapper)
        self.feed_page_placeholder = QWidget()
        self.settings_page_placeholder = QWidget()
        self.screen_stack.addWidget(self.feed_page_placeholder)
        self.screen_stack.addWidget(self.settings_page_placeholder)
        content_layout.addWidget(self.screen_stack)

        # Нижняя системная панель
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

        # 3. Парящий остров истории
        self.resume_island = QFrame(central_widget)
        self.resume_island.setObjectName("continueIsland")
        self.resume_island.setFixedSize(550, 50)
        
        island_layout = QHBoxLayout(self.resume_island)
        island_layout.setContentsMargins(20, 0, 15, 0)
        
        self.resume_label = QLabel("Продолжить просмотр: ...", self.resume_island)
        island_layout.addWidget(self.resume_label)
        island_layout.addStretch()
        
        self.resume_action_btn = QPushButton("Смотреть", self.resume_island)
        self.resume_action_btn.setObjectName("actionButton")
        self.resume_action_btn.setFixedHeight(32)
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
        y = self.height() - self.resume_island.height() - 80
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

