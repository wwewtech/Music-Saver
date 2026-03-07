import os
import threading
import time
from typing import List, Callable, Dict

from mutagen.mp3 import MP3
from mutagen.id3 import ID3, APIC
from mutagen import File as MutagenFile

from src.database.repositories import PlaylistRepository, TrackRepository
from src.database.db_manager import DBManager
from src.services.vk.driver_factory import VKDriverFactory
from src.services.vk.auth_service import AuthService
from src.services.vk.parser_service import ParserService
from src.services.vk.link_decoder import LinkDecoder
from src.services.yandex.parser_service import YandexParserService
from src.services.yandex.simple_download_service import YandexSimpleDownloadService
from src.services.download.ffmpeg_service import FFmpegService, DownloadError
from src.services.download.simple_http_service import (
    SimpleHTTPDownloadService,
    SimpleHTTPDownloadError,
)
from src.services.settings_manager import SettingsManager
from src.services.telegram.telegram_service import TelegramService
from src.domain.models import Playlist, Track
from src.domain.tagger import Tagger, sanitize_filename
from src.config import DOWNLOAD_DIR
from src.utils.logger import logger


class AppController:
    def __init__(self):
        logger.debug("Инициализация AppController...")
        self._db_manager = DBManager()
        self.playlist_repo = PlaylistRepository()
        self.track_repo = TrackRepository()
        self.settings_manager = SettingsManager()

        # Load TG settings
        settings = self.settings_manager.get_settings()
        logger.debug(f"Загруженные настройки: {settings}")
        self.telegram_service = TelegramService(
            settings.get("tg_bot_token"), settings.get("tg_chat_id")
        )

        self.driver = None
        self._login_lock = threading.Lock()
        self._is_logging_in = False

        self.is_running = False
        self.user_id = None

        # Callbacks for UI updates
        self.on_log = lambda msg: print(msg)
        self.on_progress = lambda val: None
        self.on_scan_complete = lambda playlists: None
        self.on_download_complete = lambda: None
        self.on_login_success = lambda: None

    # ── Driver management ────────────────────────────────────────────────

    def _ensure_driver(self):
        """Return existing Selenium driver or create a fresh one."""
        if self._is_driver_alive():
            return self.driver
        if self.driver:
            try:
                self.driver.quit()
            except Exception:
                pass
        self.driver = VKDriverFactory.create_driver()
        return self.driver

    def _is_driver_alive(self):
        if not self.driver:
            return False
        try:
            _ = self.driver.current_url
            return True
        except Exception:
            return False

    def save_tg_settings(self, token, chat_id):
        logger.info(
            f"Сохранение настроек Telegram: Token={token[:5]}... ChatID={chat_id}"
        )
        self.settings_manager.save_settings(token, chat_id)
        # Re-init service
        self.telegram_service = TelegramService(token, chat_id)
        return True, "Настройки сохранены."

    def get_language(self):
        return self.settings_manager.get("language", "ru")

    def set_language(self, language):
        if language in ["ru", "en"]:
            self.settings_manager.set("language", language)

    def get_preferred_source(self):
        source = self.settings_manager.get("preferred_source", "vk")
        if source not in ["vk", "yandex"]:
            return "vk"
        return source

    def set_preferred_source(self, source):
        if source in ["vk", "yandex"]:
            self.settings_manager.set("preferred_source", source)

    def get_processing_strategy(self):
        strategy = self.settings_manager.get("processing_strategy", "download_only")
        if strategy not in ["download_only", "download_upload", "direct_transfer"]:
            return "download_only"
        return strategy

    def set_processing_strategy(self, strategy):
        if strategy in ["download_only", "download_upload", "direct_transfer"]:
            self.settings_manager.set("processing_strategy", strategy)

    def is_telegram_configured(self):
        settings = self.settings_manager.get_settings()
        return bool(settings.get("tg_bot_token") and settings.get("tg_chat_id"))

    def test_tg_connection(self):
        if not self.telegram_service:
            return False, "Сервис Telegram не инициализирован."
        return self.telegram_service.send_test_message(
            "Тестовое сообщение из VK Music Saver Pro"
        )

    def get_tg_settings(self):
        return self.settings_manager.get_settings()

    def get_dashboard_stats(self):
        logger.debug("Запрос статистики для дашборда...")
        pl_count = self.playlist_repo.get_count()
        track_stats = self.track_repo.get_stats()
        download_dir = self.get_download_dir()

        # Calculate storage used
        storage_size_mb = 0
        try:
            total_size = 0
            if os.path.exists(download_dir):
                for dirpath, dirnames, filenames in os.walk(download_dir):
                    for f in filenames:
                        fp = os.path.join(dirpath, f)
                        if not os.path.islink(fp):
                            total_size += os.path.getsize(fp)
                storage_size_mb = round(total_size / (1024 * 1024), 2)
            else:
                logger.debug(f"Папка загрузок {download_dir} не найдена.")
        except Exception as e:
            logger.error(f"Error calculating storage: {e}")

        stats = {
            "playlists": pl_count,
            "tracks_total": track_stats["total"],
            "tracks_downloaded": track_stats["downloaded"],
            "tracks_uploaded": track_stats["uploaded"],
            "storage_mb": storage_size_mb,
        }
        logger.debug(f"Статистика собрана: {stats}")
        return stats

    def get_download_dir(self):
        configured_path = self.settings_manager.get("download_path", "")
        if configured_path:
            return os.path.abspath(configured_path)
        return DOWNLOAD_DIR

    @staticmethod
    def _is_valid_downloaded_audio_file(file_path: str) -> bool:
        if not os.path.exists(file_path):
            return False

        try:
            size = os.path.getsize(file_path)
            if size < 8 * 1024:
                return False

            with open(file_path, "rb") as file_obj:
                head = file_obj.read(4096).lower()
            if b"<html" in head or b"<!doctype html" in head or b"showcaptcha" in head:
                return False

            audio = MutagenFile(file_path)
            if not audio or not getattr(audio, "info", None):
                return False

            duration = float(getattr(audio.info, "length", 0.0) or 0.0)
            return duration > 1.0
        except Exception:
            return False

    def start_browser_and_login(self):
        def _task():
            with self._login_lock:
                if self._is_logging_in:
                    msg = "Вход уже выполняется. Дождитесь завершения текущей попытки."
                    self.on_log(msg)
                    logger.warning(msg)
                    return
                self._is_logging_in = True

            self.on_log("Запуск браузера...")
            logger.info("Пользователь нажал 'Войти'. Запускаем Chrome...")
            try:
                if self._is_driver_alive() and self.user_id:
                    msg = f"Браузер уже активен. Вы уже вошли (ID: {self.user_id})."
                    self.on_log(msg)
                    logger.info(msg)
                    self.on_login_success()
                    return

                if self.driver and not self._is_driver_alive():
                    try:
                        self.driver.quit()
                    except Exception:
                        pass
                    self.driver = None

                self.driver = VKDriverFactory.create_driver()
                auth_service = AuthService(self.driver)
                self.on_log("Пожалуйста, войдите в ВК...")

                uid = auth_service.wait_for_login()
                if uid:
                    self.user_id = uid
                    msg = f"Вход выполнен! ID: {uid}"
                    self.on_log(msg)
                    logger.info(msg)
                    self.on_login_success()
                else:
                    msg = "Не удалось определить ID пользователя. Возможно таймаут."
                    self.on_log(msg)
                    logger.warning(msg)
            except Exception as e:
                err_msg = f"Критическая ошибка при входе: {e}"
                self.on_log(err_msg)
                logger.exception(err_msg)
            finally:
                with self._login_lock:
                    self._is_logging_in = False

        threading.Thread(target=_task, daemon=True).start()

    def scan_playlists(self):
        def _task():
            logger.debug(f"Начало сканирования плейлистов. User ID: {self.user_id}")
            if not self.driver or not self.user_id:
                msg = "Ошибка: Браузер не запущен или нет входа."
                self.on_log(msg)
                logger.error(msg)
                return

            self.set_preferred_source("vk")
            self.on_log("Источник переключен на VK.")

            self.on_log("Сканирование плейлистов...")
            try:
                parser = ParserService(self.driver, self.user_id)
                pl_dicts = parser.scan_playlists()

                result_objects = []
                for item in pl_dicts:
                    pl = Playlist(id=item["id"], title=item["title"], url=item["url"])
                    self.playlist_repo.save(pl)
                    result_objects.append(pl)

                all_playlists = self.playlist_repo.get_all()
                msg = f"Найдено VK-плейлистов: {len(result_objects)}"
                self.on_log(msg)
                logger.info(msg)
                self.on_scan_complete(all_playlists)
            except Exception as e:
                logger.exception("Ошибка при сканировании плейлистов")
                self.on_log(f"Ошибка сканирования: {e}")

        threading.Thread(target=_task, daemon=True).start()

    def scan_yandex_chart(self):
        def _task():
            self.on_log("Открываем Яндекс.Музыку...")
            try:
                self.set_preferred_source("yandex")
                self.on_log("Источник переключен на Yandex.")
                driver = self._ensure_driver()
                parser = YandexParserService(
                    driver=driver, language=self.get_language()
                )

                self.on_log("Если открылось окно подписки — нажмите «Закрыть».")
                self.on_log(
                    "Войдите в свой аккаунт Яндекс в открывшемся браузере. Ожидаем вход..."
                )

                is_ready = parser.prepare_collection_for_manual_login(
                    login_timeout_seconds=180
                )
                if not is_ready:
                    self.on_log(
                        "Не удалось дождаться входа в Яндекс за отведенное время."
                    )
                    return

                # --- УМНЫЙ ПЕРЕХВАТ ТОКЕНА ДЛЯ СКАЧИВАНИЯ ---
                self.on_log("Получение ключа доступа (токена) для Яндекс.Музыки...")
                logger.info("Начинаем процесс получения OAuth токена...")
                driver.get(
                    "https://oauth.yandex.ru/authorize?response_type=token&client_id=23cabbbdc6cd418abb4b39c32c41195d"
                )

                ym_token = ""
                # Ждем до 30 секунд, пока страница не редиректнет нас, отдав токен
                for _ in range(30):
                    current_url = driver.current_url
                    if "access_token=" in current_url:
                        ym_token = current_url.split("access_token=")[1].split("&")[0]
                        break

                    # Пытаемся автоматически нажать на кнопку "Войти как ..." если она есть
                    try:
                        from selenium.webdriver.common.by import By

                        btns = driver.find_elements(
                            By.CSS_SELECTOR, "button[type='submit']"
                        )
                        for btn in btns:
                            if btn.is_displayed():
                                driver.execute_script("arguments[0].click();", btn)
                                time.sleep(1)
                                break
                    except Exception:
                        pass

                    time.sleep(1)

                if ym_token:
                    self.settings_manager.set("ym_token", ym_token)
                    self.on_log(
                        "✅ Ключ доступа получен! Загрузка будет работать стабильно."
                    )
                    logger.info("Токен Яндекс Музыки успешно получен.")
                else:
                    self.on_log("⚠️ Не удалось получить ключ доступа автоматически.")
                    logger.error(
                        "Таймаут получения токена Яндекс Музыки. Возможно, нужно было нажать 'Разрешить' в браузере."
                    )

                self.on_log(
                    "Переходим в «Коллекция» → «Плейлисты» и сканируем список..."
                )
                driver.get("https://music.yandex.ru/collection/playlists")
                time.sleep(2)
                # ----------------------------------------------------

                playlists_data = parser.parse_collection_playlists()

                if not playlists_data:
                    self.on_log(
                        "Плейлисты Яндекс не найдены. Проверьте, что вход выполнен и откройте «Коллекция» снова."
                    )
                    return

                added = 0
                for item in playlists_data:
                    playlist = Playlist(
                        id=item["id"],
                        title=item["title"],
                        url=item["url"],
                    )
                    self.playlist_repo.save(playlist)
                    added += 1

                all_playlists = self.playlist_repo.get_all()
                self.on_log(f"Найдено и добавлено Яндекс-плейлистов: {added}")
                self.on_scan_complete(all_playlists)
            except Exception as e:
                logger.exception("Ошибка сканирования Яндекс-плейлистов")
                self.on_log(f"Ошибка сканирования Yandex Music: {e}")

        threading.Thread(target=_task, daemon=True).start()

    def scan_yandex_playlist(self, url: str):
        """Scan a Yandex Music playlist by URL using Selenium."""
        if not url or "music.yandex" not in url:
            self.on_log("Введите корректную ссылку на плейлист Яндекс.Музыки.")
            return

        def _task():
            self.on_log("Запуск сканирования плейлиста Яндекс.Музыки...")
            try:
                self.set_preferred_source("yandex")
                self.on_log("Источник переключен на Yandex.")
                driver = self._ensure_driver()
                parser = YandexParserService(
                    driver=driver, language=self.get_language()
                )
                title, track_dicts = parser.parse_playlist_page(url)

                pl_id = YandexParserService.make_playlist_id(url)
                playlist = Playlist(id=pl_id, title=title, url=url)
                self.playlist_repo.save(playlist)

                # Cache parsed tracks so download doesn't need to re-parse
                self._ym_cached_tracks = getattr(self, "_ym_cached_tracks", {})
                self._ym_cached_tracks[pl_id] = track_dicts

                all_playlists = self.playlist_repo.get_all()
                self.on_log(f"Плейлист '{title}': найдено {len(track_dicts)} треков.")
                self.on_scan_complete(all_playlists)
            except Exception as e:
                logger.exception("Ошибка сканирования YM плейлиста")
                self.on_log(f"Ошибка сканирования Yandex Music: {e}")

        threading.Thread(target=_task, daemon=True).start()

    @staticmethod
    def _is_yandex_playlist(playlist: Playlist) -> bool:
        return playlist.id.startswith("ym:") or "music.yandex.ru" in (
            playlist.url or ""
        )

    def start_download(self, selected_playlists: List[Playlist], settings: dict):
        # settings: { "use_id3": bool, "use_covers": bool, "strategy": str }
        # Strategy: "download_only", "download_upload", "direct_transfer"
        if not selected_playlists:
            self.on_log("Не выбраны плейлисты для обработки.")
            self.on_download_complete()
            return

        self.is_running = True
        strategy = settings.get("strategy", self.get_processing_strategy())
        download_root = self.get_download_dir()

        try:
            os.makedirs(download_root, exist_ok=True)
        except Exception as e:
            self.on_log(f"Ошибка доступа к папке загрузки: {e}")
            logger.exception("Ошибка создания папки загрузки")
            self.is_running = False
            self.on_download_complete()
            return

        if (
            strategy in ["download_upload", "direct_transfer"]
            and not self.is_telegram_configured()
        ):
            warn_msg = "Telegram не настроен. Переключаемся на режим 'только скачивание на ПК'."
            self.on_log(warn_msg)
            logger.warning(warn_msg)
            strategy = "download_only"
            self.set_processing_strategy(strategy)

        def _task():
            has_vk_playlists = any(
                not self._is_yandex_playlist(pl) for pl in selected_playlists
            )
            if has_vk_playlists and not self.driver:
                self.on_log("Ошибка: Браузер не запущен. Пожалуйста, войдите в ВК.")
                self.is_running = False
                self.on_download_complete()
                return

            parser = ParserService(self.driver, self.user_id) if self.driver else None
            decoder = LinkDecoder(self.driver) if self.driver else None
            ym_parser = YandexParserService(
                driver=(
                    self.driver or self._ensure_driver()
                    if any(self._is_yandex_playlist(p) for p in selected_playlists)
                    else None
                ),
                language=self.get_language(),
            )

            logger.info(f"Запуск процесса. Стратегия: {strategy}")
            self.on_log(f"Запуск процесса. Стратегия: {strategy}")

            for pl in selected_playlists:
                if not self.is_running:
                    break

                logger.info(f"--- Обработка плейлиста: {pl.title} ---")
                self.on_log(f"--- Обработка плейлиста: {pl.title} ---")

                try:
                    # Parse Tracks
                    if self._is_yandex_playlist(pl):
                        # Try cache first (from scan), then re-parse
                        cached = getattr(self, "_ym_cached_tracks", {}).get(pl.id)
                        if cached:
                            track_dicts = cached
                        elif pl.id == "ym:chart:top100":
                            track_dicts = ym_parser.parse_chart_tracks()
                        else:
                            _, track_dicts = ym_parser.parse_playlist_page(pl.url)
                    else:
                        track_dicts = parser.parse_tracks_from_page(pl.url)
                    total = len(track_dicts)
                except Exception as e:
                    logger.exception(f"Ошибка парсинга плейлиста {pl.title}")
                    self.on_log(f"Ошибка парсинга плейлиста {pl.title}: {e}")
                    continue

                # Prepare folder
                pl_folder_name = sanitize_filename(pl.title)
                pl_dir = os.path.join(download_root, pl_folder_name)
                os.makedirs(pl_dir, exist_ok=True)

                # Prepare Telegram Topic (if uploading)
                topic_id = None
                if strategy in ["download_upload", "direct_transfer"]:
                    logger.info(f"Создание/получение темы в Telegram для: {pl.title}")
                    if self.telegram_service:
                        topic_id = self.telegram_service.create_topic(pl.title)

                for i, t_data in enumerate(track_dicts):
                    if not self.is_running:
                        break

                    progress_val = (i + 1) / total
                    self.on_progress(progress_val)

                    # Convert dict to Domain Model
                    track = Track(
                        id=t_data["id"],
                        playlist_id=pl.id,
                        artist=t_data["artist"],
                        title=t_data["title"],
                        owner_id=t_data["owner_id"],
                        audio_id=t_data["audio_id"],
                        duration=t_data.get("duration", 0),
                        subtitle=t_data.get("subtitle", ""),
                        cover_url=t_data.get("cover_url", ""),
                        access_key=t_data.get("access_key", ""),
                        url=t_data.get("url", ""),
                        action_hash=t_data.get("action_hash", ""),
                        url_hash=t_data.get("url_hash", ""),
                        album_obj=t_data.get("album_obj"),
                        main_artists=t_data.get("main_artists", []),
                        feat_artists=t_data.get("feat_artists", []),
                        genre_id=t_data.get("genre_id", 0),
                        date=t_data.get("date", 0),
                        source=t_data.get("source", "vk"),
                    )

                    self.track_repo.save(track)

                    logger.info(
                        "[TRACK_START] "
                        f"playlist='{pl.title}' track_id={track.id} source={track.source} "
                        f"idx={i + 1}/{total} has_url={bool(track.url)} duration={track.duration}"
                    )

                    safe_title = sanitize_filename(f"{track.artist} - {track.title}")[
                        :100
                    ]
                    file_name = f"{safe_title}.mp3"
                    file_path = os.path.join(pl_dir, file_name)

                    # Check existing for download
                    file_exists = False
                    if os.path.exists(file_path):
                        if self._is_valid_downloaded_audio_file(file_path):
                            file_exists = True
                        else:
                            logger.warning(
                                f"[TRACK_INVALID_LOCAL] reason=existing_file_not_audio file={file_path} size={os.path.getsize(file_path)}"
                            )
                            self.on_log(
                                f"Найден невалидный файл, перекачиваю: {safe_title}"
                            )
                            try:
                                os.remove(file_path)
                            except Exception as remove_err:
                                logger.warning(
                                    f"[TRACK_INVALID_LOCAL] failed_to_remove file={file_path} error={remove_err}"
                                )

                    if file_exists:
                        logger.info(
                            f"[TRACK_SKIP] reason=file_exists file={file_path} size={os.path.getsize(file_path)}"
                        )
                        self.on_log(f"Файл найден: {safe_title}")
                    else:
                        if track.source == "yandex":
                            # ── ИСПОЛЬЗУЕМ БЫСТРОЕ API ЯНДЕКСА ВМЕСТО БРАУЗЕРА ──
                            self.on_log(f"Yandex: скачивание: {safe_title}")
                            logger.info(
                                f"Yandex: начало скачивания через API: {safe_title}"
                            )
                            try:
                                from src.services.yandex.download_service import (
                                    YandexDownloadService,
                                )

                                ym_token = self.settings_manager.get("ym_token", "")

                                if not ym_token:
                                    msg = "❌ Ошибка: Нет токена! Вернитесь в 'Настройки', нажмите 'Сканировать Яндекс плейлисты' и дождитесь зеленого сообщения о получении ключа."
                                    self.on_log(msg)
                                    logger.error(msg)
                                    file_exists = False
                                    continue

                                ym_api = YandexDownloadService(ym_token)
                                if not ym_api.is_available():
                                    msg = "❌ Ошибка: библиотека yandex-music не инициализировалась (см. консоль)."
                                    self.on_log(msg)
                                    logger.error(msg)
                                    file_exists = False
                                    continue

                                # Разбираем ID трека
                                track_id, album_id = (
                                    YandexDownloadService.extract_ids_from_track_id(
                                        track.id
                                    )
                                )

                                # Качаем трек (библиотека сама вытянет прямую ссылку, обойдет DRM и загрузит MP3)
                                ok = ym_api.download_track(
                                    track_id, album_id, file_path
                                )

                                if ok:
                                    logger.info(
                                        f"[YM_TRACK_OK] track_id={track.id} file={file_path}"
                                    )
                                    self.on_log(f"Тегирование: {safe_title}")
                                    tag_ok = Tagger.apply_tags(
                                        file_path,
                                        track,
                                        pl.title,
                                        use_id3=settings.get("use_id3", True),
                                        use_covers=settings.get("use_covers", True),
                                    )
                                    if tag_ok:
                                        self.track_repo.update_status(
                                            track.id, "downloaded", local_path=file_path
                                        )
                                        file_exists = True
                                    else:
                                        logger.warning("Ошибка тегирования Яндекса.")
                                        file_exists = False
                                else:
                                    msg = f"Yandex: API вернул False при скачивании: {safe_title}"
                                    self.on_log(msg)
                                    logger.error(msg)
                                    file_exists = False

                            except Exception as de:
                                logger.exception(
                                    f"[YM_TRACK_FAIL] Исключение: error={de}"
                                )
                                self.on_log(f"Yandex ошибка: {de}")
                                file_exists = False
                        else:
                            # ── VK simple direct download (no tokens) with fallback ──
                            logger.info(
                                f"Файл не найден или слишком мал. Начинаем загрузку: {safe_title}"
                            )
                            self.on_log(f"Скачивание: {safe_title}")
                            direct_url = ""
                            raw_url = (t_data.get("url") or "").strip()
                            used_source = "none"
                            if raw_url.startswith("http"):
                                direct_url = raw_url
                                used_source = "raw_url"
                            if not direct_url and decoder:
                                direct_url = decoder.get_audio_url(t_data) or ""
                                if direct_url:
                                    used_source = "decoded_url"

                            if not direct_url:
                                logger.warning(
                                    "[VK_TRACK_FAIL] reason=no_direct_url "
                                    f"track_id={track.id} has_raw_url={bool(raw_url)} has_access_key={bool(track.access_key)} "
                                    f"has_action_hash={bool(track.action_hash)} has_url_hash={bool(track.url_hash)}"
                                )
                                self.on_log(f"Не удалось получить ссылку: {safe_title}")
                                file_exists = False
                            else:
                                logger.info(
                                    f"[VK_TRACK_URL] track_id={track.id} source={used_source} url_prefix={direct_url[:60]}"
                                )

                                try:
                                    logger.debug(
                                        f"Пробуем простой HTTP download для {file_path}"
                                    )
                                    SimpleHTTPDownloadService.download(
                                        direct_url, file_path
                                    )
                                    logger.info(
                                        f"Успешно скачано простым HTTP методом: {safe_title}"
                                    )
                                except SimpleHTTPDownloadError as http_err:
                                    logger.warning(
                                        f"[VK_TRACK_HTTP_FAIL] track_id={track.id} reason={http_err}"
                                    )
                                    self.on_log(
                                        f"VK: прямое скачивание не удалось, пробуем ffmpeg: {safe_title}"
                                    )
                                    try:
                                        FFmpegService.download(direct_url, file_path)
                                    except DownloadError as ff_err:
                                        logger.exception(
                                            f"[VK_TRACK_FFMPEG_FAIL] track_id={track.id} reason={ff_err}"
                                        )
                                        self.on_log(f"Ошибка загрузки: {ff_err}")
                                        file_exists = False
                                    else:
                                        logger.info(
                                            f"[VK_TRACK_FFMPEG_OK] track_id={track.id} file={file_path}"
                                        )
                                        file_exists = True
                                else:
                                    logger.info(
                                        f"[VK_TRACK_HTTP_OK] track_id={track.id} file={file_path}"
                                    )
                                    file_exists = True

                                if file_exists:
                                    logger.info(f"Применяем теги для {file_path}")
                                    self.on_log(f"Тегирование: {safe_title}")
                                    try:
                                        Tagger.apply_tags(
                                            file_path,
                                            track,
                                            pl.title,
                                            use_id3=settings.get("use_id3", True),
                                            use_covers=settings.get("use_covers", True),
                                        )
                                        self.track_repo.update_status(
                                            track.id, "downloaded", local_path=file_path
                                        )
                                        logger.info(
                                            f"Загрузка и тегирование завершены: {safe_title}"
                                        )
                                    except Exception as tag_err:
                                        logger.exception(
                                            f"Ошибка Tagger для {track.id}"
                                        )
                                        self.on_log(f"Ошибка тегирования: {tag_err}")
                                        file_exists = False

                    logger.info(
                        f"[TRACK_END] track_id={track.id} downloaded={file_exists} file={file_path}"
                    )

                    # Telegram Upload Logic
                    if file_exists and strategy in [
                        "download_upload",
                        "direct_transfer",
                    ]:
                        logger.info(
                            f"Подготовка к загрузке в TG. Стратегия={strategy}, Файл={file_path}, TopicID={topic_id}"
                        )
                        self.on_log(f"Загрузка в Telegram...")

                        # Extract Thumbnail for Telegram
                        thumbnail_data = None
                        try:
                            # Try with ID3 (mutagen)
                            audio_tags = ID3(file_path)
                            logger.debug(
                                f"Теги найдены в файле: {list(audio_tags.keys())}"
                            )

                            # Look for APIC frames
                            apic_frames = [
                                tag
                                for tag in audio_tags.values()
                                if isinstance(tag, APIC)
                            ]
                            if apic_frames:
                                # Prioritize Cover (type 3) or Other (type 0)
                                cover = next(
                                    (f for f in apic_frames if f.type == 3),
                                    apic_frames[0],
                                )
                                thumbnail_data = cover.data
                                logger.info(
                                    f"Обложка успешно извлечена. Тип: {cover.mime}, Размер: {len(thumbnail_data)} байт"
                                )
                            else:
                                logger.warning(
                                    "В тегах файла не найдены кадры APIC (обложка)."
                                )

                        except Exception as e_thumb:
                            logger.warning(
                                f"Ошибка при попытке извлечь обложку для Telegram: {e_thumb}"
                            )
                            # Fallback: check if we have cover_url and can download it again quickly?
                            # Better not to delay. Maybe track.cover_url is available?
                            # For now, just log.

                        try:
                            msg = self.telegram_service.upload_track(
                                file_path,
                                caption=f"#{sanitize_filename(pl.title).replace(' ', '_')}",
                                artist=track.artist,
                                title=track.title,
                                duration=track.duration,
                                topic_id=topic_id,
                                thumbnail=thumbnail_data,
                            )
                            if msg:
                                msg_id = str(msg.message_id)
                                file_id = msg.audio.file_id if msg.audio else None
                                logger.info(
                                    f"Трек загружен в ТГ! MessageID={msg_id} FileID={file_id}"
                                )
                                self.track_repo.update_tg_status(
                                    track.id, "uploaded", msg_id, file_id
                                )
                                self.on_log(f"TG: Успех.")

                                # Process "Direct Transfer" - Delete after upload
                                if strategy == "direct_transfer":
                                    logger.info(
                                        f"Удаление локального файла (Direct Transfer): {file_path}"
                                    )
                                    try:
                                        os.remove(file_path)
                                        self.on_log(f"Файл удален (Direct Transfer).")
                                        self.track_repo.update_status(
                                            track.id, "deleted_after_upload"
                                        )
                                    except OSError as e:
                                        logger.error(
                                            f"Не удалось удалить файл {file_path}: {e}"
                                        )
                                        self.on_log(f"Ошибка удаления файла: {e}")
                            else:
                                logger.warning(
                                    "TelegramService вернул None при загрузке."
                                )
                                self.on_log(
                                    "TG: Пропущен (сервис недоступен или ошибка)"
                                )
                                self.track_repo.update_tg_status(track.id, "failed")
                        except Exception as e:
                            logger.exception(
                                f"Исключение при выгрузке в ТГ трека {track.id}"
                            )
                            self.on_log(f"TG Ошибка: {e}")
                            self.track_repo.update_tg_status(track.id, "failed")

            self.is_running = False
            self.on_download_complete()
            logger.info("Весь процесс завершен (is_running=False)")
            self.on_log("Очередь завершена.")

        threading.Thread(target=_task, daemon=True).start()

    def close_app(self):
        logger.info("Закрытие приложения...")
        self.is_running = False
        if self.driver:
            logger.info("Закрытие Selenium Driver...")
            try:
                self.driver.quit()
            except Exception as e:
                logger.warning(f"Ошибка при закрытии Selenium Driver: {e}")
            finally:
                self.driver = None
        self._db_manager.close()
        logger.info("База данных закрыта.")
