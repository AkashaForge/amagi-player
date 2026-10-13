"""
Модуль кастомного виджета встроенного видеоплеера Amagi-Player.
Реализует абсолютно черную OLED-панель воспроизведения с пафосным 
индикатором P2P-буферизации сетей общего пользования.
"""

from PyQt6.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, QProgressBar
from PyQt6.QtCore import pyqtSignal, Qt

class MoviePlayerWidget(QWidget):
    """
    Графическая оболочка воспроизведения. Включает оверлей контроля стриминга
    и интерфейсы закрытия сессии.
    """
    # Сигнал закрытия плеера (передает текущий таймкод в секундах для сохранения в БД)
    close_player_requested = pyqtSignal(int)

    def __init__(self, parent=None):
        super().__init__(parent)
        self._current_seconds = 0 # Эмулируемый текущий таймкод просмотра
        
        self._init_player_layout()

    def _init_player_layout(self):
        """Разворачивает структуру элементов управления плеера."""
        # Устанавливаем принудительный OLED-черный фон для зоны видео
        self.setStyleSheet("background-color: #000000;")
        
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(30, 30, 30, 30)

        # 1. ВЕРХНИЙ БАР: Пафосная кнопка закрытия видеопотока
        top_bar = QHBoxLayout()
        self.exit_btn = QPushButton("✕ ЗАКРЫТЬ ТРАНСЛЯЦИЮ", self)
        self.exit_btn.setObjectName("sysButton")
        # При закрытии шлём сигнал бэкенду, чтобы тот записал секунды в user_history
        self.exit_btn.clicked.connect(lambda: self.close_player_requested.emit(self._current_seconds))
        top_bar.addWidget(self.exit_btn)
        top_bar.addStretch()
        main_layout.addLayout(top_bar)
        
        main_layout.addStretch()

        # 2. ЦЕНТРАЛЬНЫЙ ОВЕРЛЕЙ: Индикатор P2P буферизации сетей
        self.loader_container = QWidget(self)
        loader_layout = QVBoxLayout(self.loader_container)
        loader_layout.setSpacing(15)
        
        self.loader_label = QLabel("ПОСЛЕДОВАТЕЛЬНАЯ БУФЕРИЗАЦИЯ P2P ПОТОКА...", self.loader_container)
        self.loader_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.loader_label.setStyleSheet("color: #FFFFFF; font-size: 12px; font-weight: 800; letter-spacing: 3px;")
        loader_layout.addWidget(self.loader_label)

        # Ультра-тонкая белая линия прогресс-бара без рамок
        self.p2p_progress = QProgressBar(self.loader_container)
        self.p2p_progress.setFixedHeight(2)
        self.p2p_progress.setTextVisible(False)
        self.p2p_progress.setStyleSheet("""
            QProgressBar { background-color: rgba(255, 255, 255, 0.1); border: none; }
            QProgressBar::chunk { background-color: #FFFFFF; }
        """)
        self.p2p_progress.setValue(35) # Временное тестовое заполнение
        loader_layout.addWidget(self.p2p_progress)
        
        main_layout.addWidget(self.loader_container, alignment=Qt.AlignmentFlag.AlignCenter)
        
        main_layout.addStretch()

        # 3. НИЖНИЙ БАР: Шкала времени видеофайла (UX Временная заглушка)
        self.controls_bar = QWidget(self)
        controls_layout = QHBoxLayout(self.controls_bar)
        
        self.time_label = QLabel("00:00:00 / 02:15:00", self.controls_bar)
        self.time_label.setStyleSheet("color: rgba(255, 255, 255, 0.4); font-size: 11px; font-weight: 700; letter-spacing: 1px;")
        controls_layout.addWidget(self.time_label)
        controls_layout.addStretch()
        
        main_layout.addWidget(self.controls_bar)

    def set_buffering_progress(self, percentage: int):
        """Обновляет состояние P2P-бара из торрент-сервиса."""
        self.p2p_progress.setValue(percentage)
        if percentage >= 100:
            self.loader_label.setText("ВОСПРОИЗВЕДЕНИЕ КУЛЬТУРНОГО ФОНДА")
