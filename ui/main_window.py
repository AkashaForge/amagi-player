"""
Модуль главного графического окна приложения Amagi-Player.
Реализует базовую рамку интерфейса, систему слоев-страниц, парящий поиск,
угловые системные кнопки и всплывающую UX-плашку продолжения просмотра.
"""

from PyQt6.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, 
    QStackedWidget, QPushButton, QLabel, QFrame, QLineEdit
)
from PyQt6.QtCore import Qt, pyqtSignal
import os
import config

class MainWindow(QMainWindow):
    """
    Главное графическое окно приложения. Выступает визуальным каркасом
    и центральным диспетчером интерфейса.
    """
    
    # Кастомные сигналы (события) Qt для связи графики с будущим бэкендом
    theme_toggle_requested = pyqtSignal()      # Сигнал запроса смены темы
    settings_opened = pyqtSignal()            # Сигнал открытия окна настроек
    resume_movie_requested = pyqtSignal(int)  # Сигнал запуска видео из плашки истории

    def __init__(self):
        super().__init__()
        self.setWindowTitle("Amagi-Player")
        self.resize(1024, 768)
        
        # Хранилище ID фильма, отображаемого на плашке «Продолжить»
        self._current_resume_id = None
        
        # Инициализация графического ядра и макета
        self._init_ui_core()
        
        # Загрузка и применение стилей оформления QSS
        self._load_stylesheet()

    def _init_ui_core(self):
        """Создает геометрию слоев, кнопки управления и элементы UX."""
        # Центральный базовый виджет-контейнер
        central_widget = QWidget(self)
        self.setCentralWidget(central_widget)
        
        # Главный вертикальный менеджер компоновки всего окна (рамки)
        main_layout = QVBoxLayout(central_widget)
        main_layout.setContentsMargins(15, 15, 15, 15)
        main_layout.setSpacing(10)

        # --- ВЕРХНЯЯ ЧАСТЬ: ПОЛУПРОЗРАЧНЫЙ ПАРЯЩИЙ ПОИСК ---
        search_container = QWidget(self)
        search_layout = QHBoxLayout(search_container)
        search_layout.setContentsMargins(0, 0, 0, 10) # Отступ снизу до ленты
        
        self.search_bar = QLineEdit(search_container)
        self.search_bar.setObjectName("searchBar")
        self.search_bar.setPlaceholderText("Поиск фильмов по культурному фонду...")
        search_layout.addWidget(self.search_bar)
        
        main_layout.addWidget(search_container)

        # --- СРЕДНЯЯ ЧАСТЬ: МЕНЕДЖЕР ЭКРАНОВ (СТОПКА ВИДЖЕТОВ) ---
        # Позволяет переключать контент (Лента -> Карточка деталей -> Плеер)
        self.screen_stack = QStackedWidget(self)
        
        # Заготовки-заглушки для будущих экранов ленты и настроек
        self.feed_page_placeholder = QWidget()
        self.settings_page_placeholder = QWidget()
        
        self.screen_stack.addWidget(self.feed_page_placeholder)
        self.screen_stack.addWidget(self.settings_page_placeholder)
        
        main_layout.addWidget(self.screen_stack)

        # --- НИЖНЯЯ ПАНЕЛЬ СИСТЕМНЫХ КНОПОК ---
        bottom_bar = QWidget(self)
        bottom_layout = QHBoxLayout(bottom_bar)
        bottom_layout.setContentsMargins(0, 5, 0, 0)
        
        # Отодвигаем кнопки в правый нижний угол с помощью пружины (stretch)
        bottom_layout.addStretch()
        
        # Кнопка динамической смены темы
        self.theme_btn = QPushButton("Сменить тему", bottom_bar)
        self.theme_btn.setObjectName("sysButton")
        self.theme_btn.clicked.connect(self._on_theme_clicked)
        bottom_layout.addWidget(self.theme_btn)
        
        # Кнопка перехода к параметрам приложения
        self.settings_btn = QPushButton("Настройки", bottom_bar)
        self.settings_btn.setObjectName("sysButton")
        self.settings_btn.clicked.connect(self._on_settings_clicked)
        bottom_layout.addWidget(self.settings_btn)
        
        main_layout.addWidget(bottom_bar)

        # --- ЭЛЕМЕНТ UX: ОКРУГЛАЯ ВСПЛЫВАЮЩАЯ ПЛАШКА «ПРОДОЛЖИТЬ ПРОСМОТР» ---
        self.resume_panel = QFrame(self)
        self.resume_panel.setObjectName("continuePanel")
        self.resume_panel.setFixedHeight(54)
        
        resume_layout = QHBoxLayout(self.resume_panel)
        resume_layout.setContentsMargins(20, 0, 20, 0)
        
        # Информационный текст плашки
        self.resume_label = QLabel("Продолжить просмотр: ...", self.resume_panel)
        resume_layout.addWidget(self.resume_label)
        
        # Оранжевая кнопка немедленного возврата к воспроизведению
        self.resume_action_btn = QPushButton("Смотреть", self.resume_panel)
        self.resume_action_btn.setObjectName("actionButton")
        self.resume_action_btn.setFixedHeight(32)
        self.resume_action_btn.clicked.connect(self._on_resume_action_triggered)
        resume_layout.addWidget(self.resume_action_btn)
        
        # Кнопка-крестик для UX-скрытия виджета
        self.resume_close_btn = QPushButton("×", self.resume_panel)
        self.resume_close_btn.setObjectName("closePanelButton")
        self.resume_close_btn.setFixedSize(24, 24)
        self.resume_close_btn.clicked.connect(self.resume_panel.hide)
        resume_layout.addWidget(self.resume_close_btn)
        
        # Вставляем плашку в макет между экранами и нижней панелью кнопок
        main_layout.insertWidget(2, self.resume_panel)
        
        # Изначально скрываем плашку. Она активируется, если бэкенд найдет историю в БД.
        self.resume_panel.hide()

    def _load_stylesheet(self):
        """Считывает и компилирует стили из внешнего QSS файла."""
        qss_path = os.path.join(config.BASE_DIR, "ui", "styles.qss")
        if os.path.exists(qss_path):
            with open(qss_path, "r", encoding="utf-8") as f:
                self.setStyleSheet(f.read())
        else:
            print(f"[UI ПРЕДУПРЕЖДЕНИЕ]: Компонент стилей QSS отсутствует по пути {qss_path}")

    # --- ИНЖЕНЕРНЫЕ СЛОТЫ ДЛЯ ГЕНЕРАЦИИ СОБЫТИЙ (СИГНАЛОВ) ---

    def _on_theme_clicked(self):
        """Оповещает систему о клике пользователя по кнопке смены темы."""
        print("[UI ДИАГНОСТИКА]: Нажата кнопка переключения темы оформления.")
        self.theme_toggle_requested.emit()

    def _on_settings_clicked(self):
        """Переключает активный экран stacked-виджета и генерирует событие."""
        print("[UI ДИАГНОСТИКА]: Активирован переход на экран настроек.")
        # Для визуального теста переключаем стопку на индекс 1 (Экран настроек)
        self.screen_stack.setCurrentIndex(1)
        self.settings_opened.emit()

    def _on_resume_action_triggered(self):
        """Передает наверх уникальный ID фильма для инициализации стриминга."""
        if self._current_resume_id is not None:
            print(f"[UI ДИАГНОСТИКА]: Отправлен запрос на запуск плеера для ID {self._current_resume_id}")
            self.resume_movie_requested.emit(self._current_resume_id)

    # --- ИНТЕРФЕЙС УПРАВЛЕНИЯ СОСТОЯНИЕМ ВИДЖЕТОВ ---

    def show_resume_bar(self, movie_id: int, movie_title: str):
        """
        Публичный метод. Вызывается кодом связки бэкенда, когда в БД 
        обнаружен последний незавершенный просмотр.
        """
        self._current_resume_id = movie_id
        self.resume_label.setText(f"Вы остановились на просмотре фильма: <b>{movie_title}</b>")
        self.resume_panel.show()
