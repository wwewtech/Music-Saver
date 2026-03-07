import os
import threading
from typing import List, Callable

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
        self.settings_manager.save_settings(token, chat_id)
        # Re-init service
        self.telegram_service = TelegramService(token, chat_id)
        if self.telegram_service.verify_permissions():
            return True, "Настройки сохранены и проверены успешно!"
        else:
            return False, "Настройки сохранены, но проверка прав не удалась."

    def get_tg_settings(self):
        return self.settings_manager.get_settings()

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
        self.is_running = True

        def _task():
            parser = ParserService(self.driver, self.user_id)
            decoder = LinkDecoder(self.driver)

            for pl in selected_playlists:
                if not self.is_running:
                    break

                self.on_log(f"Обработка плейлиста: {pl.title}")

                # Parse Tracks
                track_dicts = parser.parse_tracks_from_page(pl.url)
                total = len(track_dicts)

                # Prepare folder
                pl_folder_name = sanitize_filename(pl.title)
                pl_dir = os.path.join(DOWNLOAD_DIR, pl_folder_name)
                os.makedirs(pl_dir, exist_ok=True)

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

                    safe_title = sanitize_filename(f"{track.artist} - {track.title}")[
                        :100
                    ]
                    file_name = f"{safe_title}.mp3"
                    file_path = os.path.join(pl_dir, file_name)

                    # Check existing
                    if os.path.exists(file_path) and os.path.getsize(file_path) > 1024:
                        self.on_log(f"Skip (exist): {safe_title}")
                        continue

                    self.on_log(f"Скачивание: {safe_title}")

                    # Get Link
                    # Since existing parser/model logic passes dict for link decoding, we might need to pass the original dict or reconstruct it partially.
                    # The LinkDecoder expects a dict with keys used in JS script ('url', 'owner_id', 'audio_id' etc.)
                    # Our Track model has these fields. Let's make a dict helper or pass attributes.
                    # Simplified: Re-use t_data which is exactly what parser gave us.

                    direct_url = decoder.get_audio_url(t_data)

                    if direct_url:
                        try:
                            FFmpegService.download(direct_url, file_path)

                            # Tagging
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

                            if self.telegram_service and self.telegram_service.verify_permissions():
                                self.on_log(f"Загрузка в Telegram: {track.title}...")
                                try:
                                    msg = self.telegram_service.upload_track(
                                        file_path,
                                        caption=f"#{sanitize_filename(pl.title).replace(' ', '_')}",
                                        artist=track.artist,
                                        title=track.title,
                                        duration=track.duration
                                    )
                                    if msg:
                                        msg_id = str(msg.message_id)
                                        file_id = msg.audio.file_id if msg.audio else None
                                        self.track_repo.update_tg_status(track.id, 'uploaded', msg_id, file_id)
                                        self.on_log(f"TG: Успешная загрузка.")
                                    else:
                                        self.track_repo.update_tg_status(track.id, 'failed')
                                except Exception as e:
                                    self.on_log(f"TG Ошибка: {e}")
                                    self.track_repo.update_tg_status(track.id, 'failed')

                            self.on_log("Готово.")

                        except DownloadError as de:
                            self.on_log(f"Ошибка загрузки: {de}")
                    else:
                        self.on_log("Не получена ссылка.")

            self.is_running = False
            self.on_download_complete()
            self.on_log("Очередь завершена.")

        threading.Thread(target=_task, daemon=True).start()

    def close_app(self):
        self.is_running = False
        if self.driver:
            self.driver.quit()
        self._db_manager.close()
