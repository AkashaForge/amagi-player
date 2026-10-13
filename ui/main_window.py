"""
Модуль кастомного виджета карточки фильма Amagi-Player.
Реализует кинопостер формата 2:3 с мягкими тенями, скруглениями 
и динамическим оверлеем информации при наведении мыши на чистом PyQt6.
"""

from PyQt6.QtWidgets import QFrame, QLabel, QPushButton, QVBoxLayout, QWidget, QGraphicsDropShadowEffect
from PyQt6.QtCore import pyqtSignal, Qt
from PyQt6.QtGui import QPixmap, QColor
import os

class MovieCardWidget(QFrame):
    """
    Интерактивный постер фильма с эффектом объема и всплывающими метаданными.
    """
    play_requested = pyqtSignal(int)

    def __init__(self, kp_id: int, title: str, year: str, cover_path: str, parent=None):
        super().__init__(parent)
        self.kp_id = kp_id
        self.title = title
        self.year = year
        self.cover_path = cover_path
        
        self.setObjectName("movieCard")
        self.setFixedSize(200, 300) 
        
        self._init_card_layout()
        self._apply_shadow_effect()

    def _init_card_layout(self):
        """Собирает внутреннюю геометрию карточки."""
        # 1. ЗАДНИЙ ПЛАН: ОБЛОЖКА ФИЛЬМА
        self.cover_label = QLabel(self)
        self.cover_label.setGeometry(0, 0, 200, 300)
        self.cover_label.setScaledContents(True)
        
        # Инженерный трюк: заставляем саму картинку скругляться по краям карточки
        self.cover_label.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        
        if self.cover_path and os.path.exists(self.cover_path):
            self.cover_label.setPixmap(QPixmap(self.cover_path))
        else:
            self.cover_label.setObjectName("coverPlaceholder")
            self.cover_label.setText(f"Обложка\\nнедоступна")
            self.cover_label.setAlignment(Qt.AlignmentFlag.AlignCenter)

        # 2. ПЕРЕДНИЙ ПЛАН: ГРАДИЕНТНЫЙ ИНФО-СЛОЙ
        self.overlay = QWidget(self)
        self.overlay.setGeometry(0, 0, 200, 300)
        
        # Эстетичный темный кинематографичный градиент
        self.overlay.setStyleSheet("""
            QWidget {
                background-color: qlineargradient(x1:0, y1:0, x2:0, y2:1, 
                                  stop:0.1 rgba(0,0,0,0), stop:0.5 rgba(0,0,0,0.5), stop:1 rgba(0,0,0,0.95));
                border-radius: 12px;
            }
        """)
        
        overlay_layout = QVBoxLayout(self.overlay)
        overlay_layout.setContentsMargins(15, 15, 15, 15)
        overlay_layout.addStretch() 
        
        # Название фильма
        self.title_label = QLabel(self.title, self.overlay)
        self.title_label.setObjectName("movieTitle")
        self.title_label.setWordWrap(True)
        overlay_layout.addWidget(self.title_label)
        
        # Год выпуска
        self.meta_label = QLabel(f"{self.year} год", self.overlay)
        self.meta_label.setObjectName("movieMeta")
        overlay_layout.addWidget(self.meta_label)
        
        overlay_layout.addSpacing(8)
        
        # Кнопка «Смотреть»
        self.watch_btn = QPushButton("Смотреть", self.overlay)
        self.watch_btn.setObjectName("actionButton")
        self.watch_btn.setFixedHeight(34)
        self.watch_btn.clicked.connect(self.watch_btn.hide) # Временный визуальный клик
        overlay_layout.addWidget(self.watch_btn)
        
        # Прячем информацию по умолчанию (концепция чистой ленты постеров)
        self.overlay.hide()

    def _apply_shadow_effect(self):
        """Создает мягкую размытую тень вокруг карточки на чистом PyQt6."""
        shadow = QGraphicsDropShadowEffect(self)
        shadow.setBlurRadius(15)                      # Радиус размытия тени
        shadow.setColor(QColor(0, 0, 0, 180))         # Мягкий черный цвет с прозрачностью
        shadow.setOffset(0, 4)                        # Сдвиг тени чуть вниз для эффекта парения
        self.setGraphicsEffect(shadow)

    # --- ТРИГГЕРЫ НАВЕДЕНИЯ МЫШИ ---
    def enterEvent(self, event):
        super().enterEvent(event)
        self.overlay.show() # Проявляем текст и кнопку при наведении

    def leaveEvent(self, event):
        super().leaveEvent(event)
        self.overlay.hide() # Скрываем, когда мышь ушла

