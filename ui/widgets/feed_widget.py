"""
Модуль кастомного виджета бесконечной ленты фильмов Amagi-Player.
Реализует пафосный разреженный заголовок раздела и скрытую область скролла
для адаптивной сетки кинопостеров в стиле OLED-минимализма.
"""

from PyQt6.QtWidgets import QWidget, QVBoxLayout, QLabel, QScrollArea, QGridLayout, QFrame
from PyQt6.QtCore import Qt

class MovieFeedWidget(QWidget):
    """
    Контейнер ленты фильмов. Управляет отображением пафосного заголовка
    и прокручиваемой сеткой карточек.
    """
    def __init__(self, parent=None):
        super().__init__(parent)
        
        self._init_feed_layout()

    def _init_feed_layout(self):
        """Собирает внутреннюю структуру ленты."""
        # Главный вертикальный макет самой ленты
        feed_layout = QVBoxLayout(self)
        feed_layout.setContentsMargins(0, 0, 0, 0)
        feed_layout.setSpacing(25) # Отступ от заголовка до сетки

        # 1. ПАФОСНЫЙ БЕЛОЙ ЗАГОЛОВК РАЗДЕЛА (В СТИЛЕ ЛОГОТИПА AMAGI)
        self.title_label = QLabel("ВЕРИФИЦИРОВАННЫЙ КУЛЬТУРНЫЙ ФОНД", self)
        self.title_label.setObjectName("sectionTitle")
        self.title_label.setStyleSheet("""
            color: #FFFFFF;
            font-size: 13px;
            font-weight: 800;
            letter-spacing: 4px;
        """)
        feed_layout.addWidget(self.title_label)

        # 2. ОБЛАСТЬ ПРОКРУТКИ С КИНЕМАТОГРАФИЧНЫМ СКРОЛЛОМ
        self.scroll_area = QScrollArea(self)
        self.scroll_area.setWidgetResizable(True)
        
        # ИСПРАВЛЕНО: Правильное обращение к перечислению Shape в PyQt6
        self.scroll_area.setFrameShape(QFrame.Shape.NoFrame)
        
        # Полностью скрываем убогий системный скроллбар Windows/Linux через QSS
        self.scroll_area.setStyleSheet("""
            QScrollArea { background-color: transparent; border: none; }
            QScrollBar:vertical { width: 0px; background: transparent; }
            QScrollBar:horizontal { height: 0px; background: transparent; }
        """)

        # 3. ВНУТРЕННИЙ КОНТЕЙНЕР ДЛЯ АДАПТИВНОЙ СЕТКИ
        self.grid_container = QWidget()
        self.grid_container.setObjectName("gridContainer")
        
        # Сетка, куда мы будем укладывать карточки MovieCardWidget
        self.grid_layout = QGridLayout(self.grid_container)
        self.grid_layout.setContentsMargins(0, 5, 0, 0)
        self.grid_layout.setSpacing(30) # Комфортные просторные отступы между постерами
        
        self.scroll_area.setWidget(self.grid_container)
        feed_layout.addWidget(self.scroll_area)

    def add_card_to_grid(self, card_widget, index: int):
        """
        Инженерный метод для динамического заполнения сетки.
        Раскладывает виджеты карточек по 4 штуки в один ряд.
        """
        row = index // 4
        col = index % 4
        self.grid_layout.addWidget(card_widget, row, col)

    def clear_grid(self):
        """Удаляет все карточки из сетки перед новым выводом или поиском."""
        while self.grid_layout.count():
            item = self.grid_layout.takeAt(0)
            widget = item.widget()
            if widget is not None:
                widget.deleteLater()
