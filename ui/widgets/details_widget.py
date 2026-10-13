"""
Модуль кастомного виджета детальной информации о фильме Amagi-Player.
Реализует просторный двухколоночный макет в стиле OLED-минимализма
с пафосными заголовками и монолитной кнопкой инициализации стриминга.
"""

from PyQt6.QtWidgets import QWidget, QHBoxLayout, QVBoxLayout, QLabel, QPushButton
from PyQt6.QtCore import pyqtSignal, Qt
from PyQt6.QtGui import QPixmap
import os

class MovieDetailsWidget(QWidget):
    """
    Экран описания фильма. Отображает метаданные из API 
    и генерирует сигнал на запуск P2P-видеопотока.
    """
    # Сигнал отправки ID фильма в торрент-сервис для старта Sequential Download
    start_streaming_requested = pyqtSignal(int)
    # Сигнал возврата обратно к сетке ленты контента
    back_to_feed_requested = pyqtSignal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self._current_kp_id = None
        self._init_details_layout()

    def _init_details_layout(self):
        """Собирает просторную геометрию экрана описания."""
        # Главный вертикальный слой экрана
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(30)

        # ВЕРХНЯЯ НАВИГАЦИЯ: Кнопка "Назад" в пафосном стиле
        nav_layout = QHBoxLayout()
        self.back_btn = QPushButton("← НАЗАД К ФОНДУ", self)
        self.back_btn.setObjectName("sysButton")
        self.back_btn.clicked.connect(self.back_to_feed_requested.emit)
        nav_layout.addWidget(self.back_btn)
        nav_layout.addStretch()
        main_layout.addLayout(nav_layout)

        # ЦЕНТРАЛЬНЫЙ БЛОК: Двухколоночный макет (Постер + Текст)
        content_layout = QHBoxLayout()
        content_layout.setSpacing(50) # Просторный отступ между колонками

        # Колонка 1: Большой постер фильма
        self.big_cover = QLabel(self)
        self.big_cover.setFixedSize(300, 450) # Увеличенный размер для акцента
        self.big_cover.setScaledContents(True)
        self.big_cover.setObjectName("coverPlaceholder")
        self.big_cover.setAlignment(Qt.AlignmentFlag.AlignCenter)
        content_layout.addWidget(self.big_cover)

        # Колонка 2: Текстовые метаданные (QVBoxLayout)
        text_layout = QVBoxLayout()
        text_layout.setSpacing(15)

        # Пафосный заглавный титул фильма
        self.title_label = QLabel("НАЗВАНИЕ ФИЛЬМА", self)
        self.title_label.setStyleSheet("color: #FFFFFF; font-size: 28px; font-weight: 900; letter-spacing: 2px;")
        self.title_label.setWordWrap(True)
        text_layout.addWidget(self.title_label)

        # Год производства
        self.year_label = QLabel("---- ГОД", self)
        self.year_label.setStyleSheet("color: rgba(255, 255, 255, 0.5); font-size: 14px; font-weight: 700; letter-spacing: 1px;")
        text_layout.addWidget(self.year_label)

        # Блок подробного текстового описания
        self.desc_label = QLabel("Загрузка описания из культурного фонда...", self)
        self.desc_label.setStyleSheet("color: rgba(255, 255, 255, 0.8); font-size: 15px; font-weight: 400; line-height: 24px;")
        self.desc_label.setWordWrap(True)
        self.desc_label.setAlignment(Qt.AlignmentFlag.AlignTop)
        text_layout.addWidget(self.desc_label)
        
        text_layout.addSpacing(20)

        # Главная монолитная белая кнопка запуска
        self.play_btn = QPushButton("ЗАПУСТИТЬ ТРАНСЛЯЦИЮ", self)
        self.play_btn.setObjectName("actionButton")
        self.play_btn.setFixedHeight(46)
        self.play_btn.setFixedWidth(280)
        self.play_btn.clicked.connect(self._on_play_clicked)
        text_layout.addWidget(self.play_btn)
        
        text_layout.addStretch() # Прижимает контент к верху колонки
        content_layout.addLayout(text_layout)
        
        main_layout.addLayout(content_layout)

    def set_movie_context(self, kp_id: int, title: str, year: str, description: str, cover_path: str):
        """
        Публичный метод интерфейса. Вызывается бэкендом при переключении экрана,
        чтобы наполнить холст оригинальными данными Кинопоиска.
        """
        self._current_kp_id = kp_id
        self.title_label.setText(title.upper())
        self.year_label.setText(f"{year} ГОД")
        self.desc_label.setText(description)
        
        if cover_path and os.path.exists(cover_path):
            self.big_cover.setPixmap(QPixmap(cover_path))
        else:
            # ИСПРАВЛЕНО: Один обратный слэш для корректного переноса строки в QLabel
            self.big_cover.setText("ОБЛОЖКА\nНЕДОСТУПНА")

    def _on_play_clicked(self):
        """Транслирует клик запуска в ядро архитектуры."""
        if self._current_kp_id is not None:
            self.start_streaming_requested.emit(self._current_kp_id)
