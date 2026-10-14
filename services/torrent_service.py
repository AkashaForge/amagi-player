"""
Модуль сервиса управления P2P-стримингом Amagi-Player.
Обеспечивает скрытый запуск фонового клиента qBittorrent, авторизацию через WebAPI,
принудительную последовательную буферизацию и асинхронный мониторинг потока.
"""

import os
import time
import subprocess
from PyQt6.QtCore import QObject, QThread, pyqtSignal
from qbittorrentapi import Client
import psutil
import config

class TorrentWorker(QThread):
    """
    Фоновый рабочий поток для асинхронного мониторинга состояния торрента.
    Предотвращает замораживание графического интерфейса при сетевых запросах к WebAPI.
    """
    # Сигнал для передачи текущего процента буферизации (0-100)
    progress_updated = pyqtSignal(int)
    # Сигнал для передачи расширенной статистики (скорость в КБ/с, количество пиров)
    stats_updated = pyqtSignal(float, int)
    # Сигнал о критической ошибке связи с P2P-клиентом
    connection_lost = pyqtSignal()

    def __init__(self, client: Client, info_hash: str):
        super().__init__()
        self.client = client
        self.info_hash = info_hash
        self._is_running = True

    def run(self):
        """Цикл периодического опроса статуса торрента в фоновом режиме."""
        while self._is_running:
            try:
                # Запрашиваем информацию о конкретном торренте по его хэшу
                torrent_info = self.client.torrents_info(torrent_hashes=self.info_hash)
                
                if torrent_info:
                    torrent = torrent_info[0]
                    
                    # Расчет прогресса загрузки в процентах (значение от 0.0 до 1.0)
                    progress_percentage = int(torrent.get("progress", 0) * 100)
                    download_speed = torrent.get("dlspeed", 0) / 1024.0  # Перевод байт/с в КБ/с
                    num_peers = torrent.get("num_peers", 0)

                    # Эмиссия сигналов в главный UI-поток
                    self.progress_updated.emit(progress_percentage)
                    self.stats_updated.emit(download_speed, num_peers)
                
            except Exception:
                self.connection_lost.emit()
                self._is_running = False
            
            # Интервал опроса WebAPI — 1 секунда
            time.sleep(1)

    def stop(self):
        """Безопасная остановка фонового цикла."""
        self._is_running = False
        self.wait()


class TorrentService(QObject):
    """
    Менеджер P2P-архитектуры плеера. Управляет подпроцессом qBittorrent,
    сессиями WebAPI и координирует фоновые потоки мониторинга.
    """
    def __init__(self):
        super().__init__()
        self.client = None
        self._process = None
        self._worker = None
        
        # Конфигурация сетевого подключения к встроенному WebUI
        self.host = "http://localhost:8080"
        self.username = "admin"
        self.password = "adminadmin"  # Стандартный пароль qBittorrent по умолчанию

    def start_engine(self) -> bool:
        """
        Инициализирует P2P-движок. Проверяет наличие запущенных процессов,
        разворачивает скрытый портативный клиент и устанавливает API-соединение.
        """
        # Предотвращаем дублирование процессов в операционной системе
        if self._is_qbittorrent_running():
            print("[P2P ЯДРО]: Обнаружен уже запущенный процесс qBittorrent. Подключение к существующему.")
        else:
            print("[P2P ЯДРО]: Запуск скрытого фонового портативного клиента...")
            if not self._spawn_hidden_process():
                return False

        # Инициализация HTTP-клиента WebAPI
        self.client = Client(host=self.host, username=self.username, password=self.password)
        
        # Выполняем серию попыток подключения (клиенту нужно время на инициализацию портов)
        for attempt in range(5):
            try:
                self.client.auth_log_in()
                print("[P2P ЯДРО]: Авторизация в WebAPI успешно пройдена.")
                
                # Принудительная настройка оптимальных параметров для стриминга видео
                self._apply_streaming_preferences()
                return True
            except Exception:
                print(f"[P2P ЯДРО]: Ожидание готовности WebAPI (Попытка {attempt + 1}/5)...")
                time.sleep(2)
        
        return False

    def start_streaming(self, magnet_link: str, progress_callback, stats_callback) -> str:
        """
        Добавляет раздачу в очередь, форсирует режим последовательного скачивания
        и запускает асинхронный поток мониторинга прогресса.
        Возвращает уникальный инфо-хэш добавленного торрента.
        """
        try:
            # 1. Добавление ссылки в торрент-клиент
            self.client.torrents_add(urls=magnet_link)
            
            # Пауза для того, чтобы клиент успел распарсить magnet и сгенерировать хэш
            time.sleep(1.5)
            
            # Получаем список торрентов, чтобы определить хэш последней добавленной раздачи
            torrents = self.client.torrents_info(sort="added_on", reverse=True)
            if not torrents:
                raise RuntimeError("Не удалось получить информацию о добавленном торренте.")
            
            target_torrent = torrents[0]
            info_hash = target_torrent["hash"]

            # 2. АКТИВАЦИЯ СТРИМИНГОВЫХ РЕЖИМОВ
            # Включаем последовательную загрузку (блоки качаются строго от 0 до конца файла)
            self.client.torrents_toggle_sequential_download(torrent_hashes=info_hash)
            # Форсируем приоритет для первого и последнего блоков (необходимо для чтения индексов плеером)
            self.client.torrents_toggle_first_last_piece_priority(torrent_hashes=info_hash)

            # 3. ИНИЦИАЛИЗАЦИЯ ПОТОКА МОНИТОРИНГА
            if self._worker and self._worker.isRunning():
                self._worker.stop()

            self._worker = TorrentWorker(self.client, info_hash)
            # Связываем внутренние сигналы рабочего потока с внешними колбэками UI
            self._worker.progress_updated.connect(progress_callback)
            self._worker.stats_updated.connect(stats_callback)
            self._worker.start()

            print(f"[P2P ЯДРО]: Стриминг активирован для хэша: {info_hash}")
            return info_hash

        except Exception as e:
            print(f"[P2P ОШИБКА СТРИМИНГА]: {e}")
            return ""

    def stop_streaming(self):
        """Останавливает мониторинг текущей сессии буферизации."""
        if self._worker:
            print("[P2P ЯДРО]: Остановка фонового мониторинга потока.")
            self._worker.stop()
            self._worker = None

    def shutdown_engine(self):
        """Полная остановка P2P-движка и корректное закрытие фонового процесса."""
        self.stop_streaming()
        if self.client:
            try:
                # Даем команду самому приложению qBittorrent завершить работу
                self.client.application_shutdown()
                print("[P2P ЯДРО]: Отправлена команда выключения приложения qBittorrent.")
            except Exception:
                pass
        
        # Жесткая очистка процесса, если он завис в памяти Windows
        if self._process:
            self._process.terminate()

    def _is_qbittorrent_running(self) -> bool:
        """Сканирует системные процессы операционной системы на наличие qbittorrent."""
        for proc in psutil.process_iter(['name']):
            if proc.info['name'] and 'qbittorrent' in proc.info['name'].lower():
                return True
        return False

    def _spawn_hidden_process(self) -> bool:
        """Осуществляет низкоуровневый запуск бинарного файла Windows в изолированном режиме."""
        if not os.path.exists(config.QBITTORRENT_EXE):
            print(f"[КРИТИЧЕСКАЯ ОШИБКА]: Исполняемый файл не найден по пути: {config.QBITTORRENT_EXE}")
            return False

        # Гарантируем наличие физической директории для портативного профиля
        os.makedirs(config.QBITTORRENT_PROFILE, exist_ok=True)

        # Конструируем аргументы запуска для изоляции конфигурации
        cmd = [
            config.QBITTORRENT_EXE,
            f"--profile={config.QBITTORRENT_PROFILE}",
            "--webui-port=8080"
        ]

        try:
            # Используем флаг скрытия консольного окна операционной системы (только для Windows OS)
            creation_flags = subprocess.CREATE_NO_WINDOW
            
            self._process = subprocess.Popen(
                cmd,
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
                creationflags=creation_flags
            )
            return True
        except Exception as e:
            print(f"[КРИТИЧЕСКАЯ ОШИБКА ЗАПУСКА EXE]: {e}")
            return False

    def _apply_streaming_preferences(self):
        """Устанавливает оптимальные глобальные параметры WebAPI для непрерывного медиа-стриминга."""
        preferences = {
            "queueing_enabled": False,         # Отключаем ограничение очереди (качаем сразу)
            "listen_port": 6881,               # Фиксированный стандартный порт для входящих пиров
            "upnp": True,                      # Автоматический проброс портов на роутере
            "max_connec": 200,                 # Ограничение соединений, чтобы не перегружать домашний роутер
        }
        try:
            self.client.app_set_preferences(preferences=preferences)
        except Exception as e:
            print(f"[P2P ЯДРО]: Не удалось применить глобальные настройки: {e}")
