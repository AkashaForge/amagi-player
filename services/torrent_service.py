"""
Менеджер P2P-архитектуры плеера. Управляет подпроцессом qBittorrent,
сессиями WebAPI, зачисткой памяти ОС и координирует фоновые потоки.
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
    Предотвращает блокировку графического интерфейса при сетевых запросах к WebAPI.
    """
    progress_updated = pyqtSignal(int)
    stats_updated = pyqtSignal(float, int)
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
                torrent_info = self.client.torrents_info(torrent_hashes=self.info_hash)
                
                if torrent_info:
                    torrent = torrent_info[0] if isinstance(torrent_info, list) else torrent_info
                    
                    progress_percentage = int(torrent.get("progress", 0) * 100)
                    download_speed = torrent.get("dlspeed", 0) / 1024.0  # Перевод в КБ/с
                    num_peers = torrent.get("num_peers", 0)

                    self.progress_updated.emit(progress_percentage)
                    self.stats_updated.emit(download_speed, num_peers)
                
            except Exception:
                self.connection_lost.emit()
                self._is_running = False
            
            time.sleep(1)

    def stop(self):
        """Безопасная остановка фонового цикла."""
        self._is_running = False
        self.wait()


class TorrentService(QObject):
    """
    Менеджер P2P-архитектуры плеера. Управляет подпроцессом qBittorrent,
    сессиями WebAPI, зачисткой памяти ОС и координирует фоновые потоки.
    """
    def __init__(self):
        super().__init__()
        self.client = None
        self._process = None
        self._worker = None
        
        self.host = "http://localhost:8080"
        self.username = "admin"
        self.password = "adminadmin"

    def start_engine(self) -> bool:
        """
        Инициализирует P2P-движок. Проверяет наличие зависших процессов,
        принудительно зачищает их, разворачивает чистый скрытый клиент и устанавливает API-соединение.
        """
        if self._is_qbittorrent_running():
            print("[P2P ЯДРО]: Обнаружен старый зависший процесс qBittorrent после падения. Зачистка...")
            self._kill_old_qbittorrent()

        # Разворачиваем чистый скрытый фоновый портативный клиент
        print("[P2P ЯДРО]: Запуск скрытого фонового портативного клиента...")
        if not self._spawn_hidden_process():
            return False

        # Даем ОС и клиенту гарантированное время на запуск сокетов перед авторизацией
        time.sleep(3)

        # Инициализация HTTP-клиента WebAPI
        self.client = Client(host=self.host, username=self.username, password=self.password)
        
        # Выполняем серию попыток подключения
        for attempt in range(7):
            try:
                self.client.auth_log_in()
                print("[P2P ЯДРО]: Авторизация в WebAPI успешно пройдена.")
                self._apply_streaming_preferences()
                return True
            except Exception:
                print(f"[P2P ЯДРО]: Ожидание готовности WebAPI (Попытка {attempt + 1}/7)...")
                time.sleep(2)
        
        return False

    def start_streaming(self, magnet_link: str, progress_callback, stats_callback) -> str:
        """Добавляет раздачу в очередь, форсирует стриминг-режимы и запускает поток мониторинга."""
        try:
            self.client.torrents_add(urls=magnet_link)
            time.sleep(1.5)
            
            torrents = self.client.torrents_info(sort="added_on", reverse=True)
            if not torrents:
                raise RuntimeError("Не удалось получить информацию о добавленном торренте.")
            
            target_torrent = torrents[0]
            info_hash = target_torrent["hash"]

            # АКТИВАЦИЯ СТРИМИНГОВЫХ РЕЖИМОВ
            self.client.torrents_toggle_sequential_download(torrent_hashes=info_hash)
            self.client.torrents_toggle_first_last_piece_priority(torrent_hashes=info_hash)

            if self._worker and self._worker.isRunning():
                self._worker.stop()

            self._worker = TorrentWorker(self.client, info_hash)
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
                self.client.application_shutdown()
                print("[P2P ЯДРО]: Отправлена команда выключения приложения qBittorrent.")
            except Exception:
                pass
        
        if self._process:
            self._process.terminate()

    def _is_qbittorrent_running(self) -> bool:
        """Сканирует системную таблицу процессов на наличие запущенного qbittorrent."""
        for proc in psutil.process_iter(['name']):
            try:
                if proc.info['name'] and 'qbittorrent' in proc.info['name'].lower():
                    return True
            except (psutil.NoSuchProcess, psutil.AccessDenied):
                continue
        return False

    def _kill_old_qbittorrent(self):
        """Находит и принудительно завершает зависший в памяти процесс."""
        for proc in psutil.process_iter(['name']):
            try:
                if proc.info['name'] and 'qbittorrent' in proc.info['name'].lower():
                    proc.kill()
                    proc.wait(timeout=2)
                    print("[P2P ЯДРО]: Старый зависший процесс успешно уничтожен.")
            except (psutil.NoSuchProcess, psutil.AccessDenied):
                continue

    def _spawn_hidden_process(self) -> bool:
        """Осуществляет низкоуровневый запуск бинарного файла в полностью изолированном скрытом режиме."""
        if not os.path.exists(config.QBITTORRENT_EXE):
            print(f"[КРИТИЧЕСКАЯ ОШИБКА]: Исполняемый файл не найден по пути: {config.QBITTORRENT_EXE}")
            return False

        # Гарантируем наличие физической директории для портативного изолированного профиля
        config_dir = os.path.join(config.QBITTORRENT_PROFILE, "qBittorrent")
        os.makedirs(config_dir, exist_ok=True)

        # 🧠 ТРЮК С ПРЕД-НАСТРОЙКОЙ (ИНЪЕКЦИЯ КОНФИГА):
        # Записываем файл конфигурации .ini ДО старта exe. 
        # Это мгновенно отключает опасные сетевые порты, которые триггерят Windows Firewall у юзера.
        ini_path = os.path.join(config_dir, "qBittorrent.ini")
        if not os.path.exists(ini_path):
            with open(ini_path, "w", encoding="utf-8") as f:
                f.write(
                    "[Preferences]\n"
                    "Connection\\PortRangeMin=0\n"        # Отключает фиксированный порт (ставит случайный исходящий)
                    "Connection\\UPnP=false\n"             # Выключает UPnP (убирает триггер брандмауэра)
                    "Connection\\UPnPVMNATPMP=false\n"
                    "WebUI\\Enabled=true\n"                # Сразу активирует WebUI внутри песочницы
                    "WebUI\\Port=8080\n"
                    "WebUI\\LocalHostAuth=false\n"         # Отключает лишние окна аутентификации на localhost
                    "WebUI\\AuthSubnetWhitelistEnabled=false\n"
                )

        cmd = [
            config.QBITTORRENT_EXE,
            f"--profile={config.QBITTORRENT_PROFILE}",
            "--webui-port=8080",
            "--no-splash",
            "--minimized"
        ]

        try:
            # Настройка STARTUPINFO для жесткого подавления GUI на уровне ядра Windows
            startupinfo = subprocess.STARTUPINFO()
            startupinfo.dwFlags |= subprocess.STARTF_USESHOWWINDOW
            startupinfo.wShowWindow = subprocess.SW_HIDE
            
            self._process = subprocess.Popen(
                cmd,
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
                startupinfo=startupinfo,
                creationflags=subprocess.CREATE_NO_WINDOW
            )
            return True
        except Exception as e:
            print(f"[КРИТИЧЕСКАЯ ОШИБКА ЗАПУСКА EXE]: {e}")
            return False

    def _apply_streaming_preferences(self):
        """Устанавливает оптимальные глобальные параметры WebAPI для непрерывного медиа-стриминга."""
        preferences = {
            "queueing_enabled": False,         # Отключаем очереди, качаем поток немедленно
            "max_connec": 100,                 # Ограничиваем сессии, чтобы не перегружать сокеты юзера
        }
        try:
            self.client.app_set_preferences(preferences=preferences)
            print("[P2P ЯДРО]: Потоковые параметры успешно оптимизированы.")
        except Exception as e:
            print(f"[P2P ЯДРО]: Не удалось применить глобальные настройки: {e}")
