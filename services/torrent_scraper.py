"""
Модуль автоматического поиска P2P-потоков (Torrent Scraper).
Реализует гибкую, заменяемую архитектуру провайдеров поиска (Internet Archive / RuTracker)
и автоматическую генерацию magnet-ссылок на основе метаданных Кинопоиска.
"""

import requests
import urllib.parse
from abc import ABC, abstractmethod
import config

class BaseTorrentProvider(ABC):
    """
    Абстрактный класс (интерфейс) для P2P-провайдеров.
    Любой новый поисковик (RuTracker, Archive и т.д.) должен наследоваться от него.
    """
    @abstractmethod
    def search_magnet(self, title_ru: str, title_orig: str, year: str) -> str:
        """Принимает метаданные фильма и возвращает готовую magnet-ссылку или пустую строку."""
        pass


class InternetArchiveProvider(BaseTorrentProvider):
    """
    Провайдер для поиска по официальному публичному API Internet Archive (archive.org).
    Ищет строго легальный контент Общественного достояния по оригинальному названию.
    """
    def __init__(self):
        self.search_url = "https://archive.org"

    def search_magnet(self, title_ru: str, title_orig: str, year: str) -> str:
        # Для Архива критически важно искать по оригинальному английскому названию
        search_title = title_orig if title_orig and title_orig != "Без названия" else title_ru
        if not search_title:
            return ""
            
        # Формируем строгий поисковый запрос для API Archive.org: название, год и медиа-тип "кино"
        clean_title = search_title.replace(":", "").replace("-", " ")
        query = f"title:({clean_title}) AND year:{year} AND mediatype:movies"
        
        params = {
            "q": query,
            "fl[]": "identifier,item_size", # Запрашиваем уникальный ID раздачи
            "sort[]": "downloads desc",    # Выбираем самые скачиваемые (где больше всего живых пиров)
            "output": "json",
            "rows": 3
        }
        
        try:
            response = requests.get(self.search_url, params=params, timeout=6)
            if response.status_code == 200:
                docs = response.json().get("response", {}).get("docs", [])
                if not docs:
                    print(f"[ARCHIVE PROVIDER]: По запросу '{query}' ничего не найдено.")
                    return ""
                
                # Берем самый популярный релиз
                best_match = docs[0]
                identifier = best_match.get("identifier")
                
                # Archive.org автоматически раздает все свои элементы по протоколу BitTorrent.
                # Мы можем на лету собрать стандартный magnet, зная внутренний идентификатор раздачи:
                encoded_dn = urllib.parse.quote(identifier)
                magnet_link = (
                    f"magnet:?xt=urn:btih:{identifier.md5() if hasattr(identifier, 'md5') else ''}" 
                    f"&dn={encoded_dn}"
                    f"&tr=http://archive.org"
                )
                
                # Примечание: API Архива отдает идентификатор. Для qBittorrent надежнее скачать 
                # их готовый .torrent файл, который лежит по фиксированному адресу:
                direct_torrent_url = f"https://archive.org{identifier}/{identifier}_archive.torrent"
                
                print(f"[ARCHIVE PROVIDER]: Найдена легальная раздача: {direct_torrent_url}")
                # Наш TorrentService (qBittorrent) умеет принимать как magnet-строку, так и прямой URL на .torrent файл!
                return direct_torrent_url
                
            return ""
        except Exception as e:
            print(f"[ARCHIVE ERROR]: Ошибка парсинга Архива: {e}")
            return ""


class RuTrackerProvider(BaseTorrentProvider):
    """
    Заглушка-провайдер для RuTracker (или альтернативных индексов).
    Демонстрирует, как легко переключить логику на поиск по русскому названию.
    """
    def __init__(self):
        # Здесь будет эндпоинт вашего API-парсера Рутрекера или Jackett
        self.api_url = "https://apibay.org" 

    def search_magnet(self, title_ru: str, title_orig: str, year: str) -> str:
        # Рутрекер отлично ищет по русскому названию
        query = f"{title_ru} {year}".strip()
        print(f"[RUTRACKER PROVIDER]: Запуск парсинга по СНГ-базе для: '{query}'")
        
        try:
            # Эмуляция запроса к поисковому аггрегатору
            response = requests.get(self.api_url, params={"q": query}, timeout=6)
            if response.status_code == 200:
                torrents = response.json()
                if torrents and isinstance(torrents, list) and torrents[0].get("id") != "0":
                    best = max(torrents, key=lambda x: int(x.get("seeders", 0)))
                    info_hash = best.get("info_hash")
                    return f"magnet:?xt=urn:btih:{info_hash}&dn={urllib.parse.quote(best.get('name'))}"
            return ""
        except Exception:
            return ""


class TorrentScraper:
    """
    Диспетчер скрейпинга. Управляет активным провайдером на основе конфигурации.
    """
    def __init__(self):
        # Динамически выбираем провайдера на основе флага в config.py
        # Добавьте в config.py строку: P2P_PROVIDER = "archive" (или "rutracker")
        provider_type = getattr(config, "P2P_PROVIDER", "archive").lower()
        
        if provider_type == "archive":
            self.provider = InternetArchiveProvider()
            print("[SCRAPER]: Активирован легальный провайдер Internet Archive.")
        else:
            self.provider = RuTrackerProvider()
            print("[SCRAPER]: Активирован альтернативный провайдер (RuTracker/Агрегатор).")

    def find_best_magnet(self, title_ru: str, title_orig: str, year: str) -> str:
        """Перенаправляет запрос в выбранный активный провайдер."""
        return self.provider.search_magnet(title_ru, title_orig, year)
