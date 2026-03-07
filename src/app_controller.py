import os
import threading
import time
from typing import List, Callable, Dict

from mutagen.mp3 import MP3
from mutagen.id3 import ID3, APIC

from src.database.repositories import PlaylistRepository, TrackRepository
from src.database.db_manager import DBManager
from src.services.vk.driver_factory import VKDriverFactory
from src.services.vk.auth_service import AuthService
from src.services.vk.parser_service import ParserService
from src.services.vk.link_decoder import LinkDecoder
from src.services.download.ffmpeg_service import FFmpegService, DownloadError
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
        self.telegram_service = TelegramService(settings.get('tg_bot_token'), settings.get('tg_chat_id'))

        self.driver = None

        self.is_running = False
        self.user_id = None

        # Callbacks for UI updates
        self.on_log = lambda msg: print(msg)
        self.on_progress = lambda val: None
        self.on_scan_complete = lambda playlists: None
        self.on_download_complete = lambda: None
        self.on_login_success = lambda: None

    def save_tg_settings(self, token, chat_id):
        logger.info(f"Сохранение настроек Telegram: Token={token[:5]}... ChatID={chat_id}")
        self.settings_manager.save_settings(token, chat_id)
        # Re-init service
        self.telegram_service = TelegramService(token, chat_id)
        return True, "Настройки сохранены locally."

    def test_tg_connection(self):
        if not self.telegram_service:
            return False, "Сервис Telegram не инициализирован."
        return self.telegram_service.send_test_message("Test message from VK Music Saver Pro")

    def get_tg_settings(self):
        return self.settings_manager.get_settings()
        
    def get_dashboard_stats(self):
        logger.debug("Запрос статистики для дашборда...")
        pl_count = self.playlist_repo.get_count()
        track_stats = self.track_repo.get_stats()
        
        # Calculate storage used
        storage_size_mb = 0
        try:
            total_size = 0
            if os.path.exists(DOWNLOAD_DIR):
                for dirpath, dirnames, filenames in os.walk(DOWNLOAD_DIR):
                    for f in filenames:
                        fp = os.path.join(dirpath, f)
                        if not os.path.islink(fp):
                            total_size += os.path.getsize(fp)
                storage_size_mb = round(total_size / (1024 * 1024), 2)
            else:
                logger.debug(f"Папка загрузок {DOWNLOAD_DIR} не найдена.")
        except Exception as e:
            logger.error(f"Error calculating storage: {e}")
            
        stats = {
            "playlists": pl_count,
            "tracks_total": track_stats["total"],
            "tracks_downloaded": track_stats["downloaded"],
            "tracks_uploaded": track_stats["uploaded"],
            "storage_mb": storage_size_mb
        }
        logger.debug(f"Статистика собрана: {stats}")
        return stats

    def start_browser_and_login(self):
        def _task():
            self.on_log("Запуск браузера...")
            logger.info("Пользователь нажал 'Войти'. Запускаем Chrome...")
            try:
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

        threading.Thread(target=_task, daemon=True).start()

    def scan_playlists(self):
        def _task():
            logger.debug(f"Начало сканирования плейлистов. User ID: {self.user_id}")
            if not self.driver or not self.user_id:
                msg = "Ошибка: Браузер не запущен или нет входа."
                self.on_log(msg)
                logger.error(msg)
                return

            self.on_log("Сканирование плейлистов...")
            try:
                parser = ParserService(self.driver, self.user_id)
                pl_dicts = parser.scan_playlists()

                result_objects = []
                for item in pl_dicts:
                    pl = Playlist(id=item['id'], title=item['title'], url=item['url'])
                    self.playlist_repo.save(pl)
                    result_objects.append(pl)

                msg = f"Найдено плейлистов: {len(result_objects)}"
                self.on_log(msg)
                logger.info(msg)
                self.on_scan_complete(result_objects)
            except Exception as e:
                logger.exception("Ошибка при сканировании плейлистов")
                self.on_log(f"Ошибка сканирования: {e}")

        threading.Thread(target=_task, daemon=True).start()

    def start_download(self, selected_playlists: List[Playlist], settings: dict):
        # settings: { "use_id3": bool, "use_covers": bool, "strategy": str }
        # Strategy: "download_only", "download_upload", "direct_transfer"
        self.is_running = True
        strategy = settings.get("strategy", "download_only")

        def _task():
            if not self.driver:
                self.on_log("Ошибка: Браузер не запущен. Пожалуйста, войдите в ВК.")
                self.is_running = False
                self.on_download_complete()
                return

            parser = ParserService(self.driver, self.user_id)
            decoder = LinkDecoder(self.driver)
            
            logger.info(f"Запуск процесса. Стратегия: {strategy}")
            self.on_log(f"Запуск процесса. Стратегия: {strategy}")

            for pl in selected_playlists:
                if not self.is_running:
                    break

                logger.info(f"--- Обработка плейлиста: {pl.title} ---")
                self.on_log(f"--- Обработка плейлиста: {pl.title} ---")

                try:
                    # Parse Tracks
                    track_dicts = parser.parse_tracks_from_page(pl.url)
                    total = len(track_dicts)
                except Exception as e:
                    logger.exception(f"Ошибка парсинга плейлиста {pl.title}")
                    self.on_log(f"Ошибка парсинга плейлиста {pl.title}: {e}")
                    continue

                # Prepare folder
                pl_folder_name = sanitize_filename(pl.title)
                pl_dir = os.path.join(DOWNLOAD_DIR, pl_folder_name)
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
                    )

                    self.track_repo.save(track)

                    safe_title = sanitize_filename(f"{track.artist} - {track.title}")[:100]
                    file_name = f"{safe_title}.mp3"
                    file_path = os.path.join(pl_dir, file_name)

                    # Check existing for download
                    file_exists = os.path.exists(file_path) and os.path.getsize(file_path) > 1024
                    
                    if file_exists:
                         logger.info(f"Файл уже существует на диске (размер > 1кб): {file_path}")
                         self.on_log(f"Файл найден: {safe_title}")
                    else:
                        logger.info(f"Файл не найден или слишком мал. Начинаем загрузку: {safe_title}")
                        self.on_log(f"Скачивание: {safe_title}")
                        direct_url = decoder.get_audio_url(t_data)
                        if direct_url:
                            logger.debug(f"Получена прямая ссылка для {track.id}: {direct_url[:50]}...")
                            try:
                                logger.debug(f"Вызов FFmpegService для {file_path}")
                                FFmpegService.download(direct_url, file_path)
                                # Tagging
                                logger.info(f"Применяем теги для {file_path}")
                                self.on_log(f"Тегирование: {safe_title}")
                                Tagger.apply_tags(
                                    file_path,
                                    track,
                                    pl.title,
                                    use_id3=settings.get("use_id3", True),
                                    use_covers=settings.get("use_covers", True),
                                )
                                self.track_repo.update_status(track.id, "downloaded", local_path=file_path)
                                file_exists = True
                                logger.info(f"Загрузка и тегирование завершены: {safe_title}")
                            except Exception as de:
                                logger.exception(f"Ошибка в FFmpeg или Tagger для {track.id}")
                                self.on_log(f"Ошибка загрузки/ffmpeg: {de}")
                                file_exists = False
                        else:
                            logger.warning(f"LinkDecoder не смог вытащить ссылку для трека {track.id}")
                            self.on_log(f"Не удалось получить ссылку: {safe_title}")
                            file_exists = False

                    # Telegram Upload Logic
                    if file_exists and strategy in ["download_upload", "direct_transfer"]:
                        logger.info(f"Подготовка к загрузке в TG. Стратегия={strategy}, Файл={file_path}, TopicID={topic_id}")
                        self.on_log(f"Загрузка в Telegram...")

                        # Extract Thumbnail for Telegram
                        thumbnail_data = None
                        try:
                            # Try with ID3 (mutagen)
                            audio_tags = ID3(file_path)
                            logger.debug(f"Теги найдены в файле: {list(audio_tags.keys())}")
                            
                            # Look for APIC frames
                            apic_frames = [tag for tag in audio_tags.values() if isinstance(tag, APIC)]
                            if apic_frames:
                                # Prioritize Cover (type 3) or Other (type 0)
                                cover = next((f for f in apic_frames if f.type == 3), apic_frames[0])
                                thumbnail_data = cover.data
                                logger.info(f"Обложка успешно извлечена. Тип: {cover.mime}, Размер: {len(thumbnail_data)} байт")
                            else:
                                logger.warning("В тегах файла не найдены кадры APIC (обложка).")
                                
                        except Exception as e_thumb:
                            logger.warning(f"Ошибка при попытке извлечь обложку для Telegram: {e_thumb}")
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
                                thumbnail=thumbnail_data
                            )
                            if msg:
                                msg_id = str(msg.message_id)
                                file_id = msg.audio.file_id if msg.audio else None
                                logger.info(f"Трек загружен в ТГ! MessageID={msg_id} FileID={file_id}")
                                self.track_repo.update_tg_status(track.id, 'uploaded', msg_id, file_id)
                                self.on_log(f"TG: Успех.")
                                
                                # Process "Direct Transfer" - Delete after upload
                                if strategy == "direct_transfer":
                                    logger.info(f"Удаление локального файла (Direct Transfer): {file_path}")
                                    try:
                                        os.remove(file_path)
                                        self.on_log(f"Файл удален (Direct Transfer).")
                                        self.track_repo.update_status(track.id, "deleted_after_upload")
                                    except OSError as e:
                                        logger.error(f"Не удалось удалить файл {file_path}: {e}")
                                        self.on_log(f"Ошибка удаления файла: {e}")
                            else:
                                logger.warning("TelegramService вернул None при загрузке.")
                                self.on_log("TG: Пропущен (сервис недоступен или ошибка)")
                                self.track_repo.update_tg_status(track.id, 'failed')
                        except Exception as e:
                            logger.exception(f"Исключение при выгрузке в ТГ трека {track.id}")
                            self.on_log(f"TG Ошибка: {e}")
                            self.track_repo.update_tg_status(track.id, 'failed')

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
            self.driver.quit()
        self._db_manager.close()
        logger.info("База данных закрыта.")
