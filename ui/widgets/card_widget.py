"""
Модуль кастомного виджета карточки фильма Amagi-Player.
Реализует скругленную карточку фильма (Обложка + Название) 
в стиле OLED-минимализма с обработкой клика для запуска трансляции.
"""

from PyQt6.QtWidgets import QWidget, QVBoxLayout, QLabel
from PyQt6.QtCore import pyqtSignal, Qt
from PyQt6.QtGui import QPixmap
import os

class MovieCardWidget(QWidget):
    """
    Скругленная карточка фильма для адаптивной сетки.
    Генерирует сигнал play_requested при клике на неё.
    """
    # Сигнал, который требует run_ui_test.py для открытия экрана деталей
    play_requested = pyqtSignal(int)

    def __init__(self, kp_id: int, title: str, year: str, cover_path: str, parent=None):
        super().__init__(parent)
        self.kp_id = kp_id
        self.title = title
        self.year = year
        self.cover_path = cover_path
        
        self._init_card_layout()

    def _init_card_layout(self):
        # Настраиваем размеры карточки под пафосный кинематографичный стиль
        self.setFixedSize(220, 360)
        self.setCursor(Qt.CursorShape.PointingHandCursor) # Меняем курсор при наведении
        
        # Основной вертикальный контейнер карточки
        layout = QVBoxLayout(self)
        layout.setContentsMargins(5, 5, 5, 5)
        layout.setSpacing(10)

        # 1. ОБЛОЖКА ФИЛЬМА
        self.cover_label = QLabel(self)
        self.cover_label.setFixedSize(210, 300)
        self.cover_label.setScaledContents(True)
        self.cover_label.setObjectName("coverPlaceholder")
        self.cover_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        
        if self.cover_path and os.path.exists(self.cover_path):
            self.cover_label.setPixmap(QPixmap(self.cover_path))
        else:
            self.cover_label.setText("ОБЛОЖКА\nНЕДОСТУПНА")
            self.cover_label.setStyleSheet("""
                background-color: #111111; 
                color: rgba(255, 255, 255, 0.3); 
                font-weight: 700; 
                font-size: 11px;
                border: 1px solid rgba(255, 255, 255, 0.05);
            """)
        layout.addWidget(self.cover_label)

        # 2. НАЗВАНИЕ ФИЛЬМА (В верхнем регистре, как в дизайне)
        self.title_label = QLabel(self.title.upper(), self)
        self.title_label.setStyleSheet("""
            color: #FFFFFF; 
            font-size: 12px; 
            font-weight: 800; 
            letter-spacing: 1px;
        """)
        self.title_label.setWordWrap(False) # В одну строку с затуханием/обрезанием
        layout.addWidget(self.title_label)

        # 3. ГОД
        self.year_label = QLabel(f"{self.year} ГОД", self)
        self.year_label.setStyleSheet("""
            color: rgba(255, 255, 255, 0.4); 
            font-size: 10px; 
            font-weight: 700;
        """)
        layout.addWidget(self.year_label)
        
        layout.addStretch()

    def mousePressEvent(self, event):
        """Перехватываем клик мыши по любой точке карточки"""
        if event.button() == Qt.MouseButton.LeftButton:
            # Отправляем ID фильма в run_ui_test.py
            self.play_requested.emit(self.kp_id)
        super().mousePressEvent(event)
