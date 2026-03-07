import requests
import re
from datetime import datetime
from mutagen.mp3 import MP3
from mutagen.id3 import (
    ID3,
    TIT2,
    TPE1,
    TPE2,
    TALB,
    TDRC,
    TCON,
    COMM,
    APIC,
    WOAR,
    WOAS,
    WOAF,
    TLEN,
)

from src.config import VK_GENRES
from src.domain.models import Track
from src.utils.logger import logger


class Tagger:
    @staticmethod
    def apply_tags(
        filepath: str,
        track: Track,
        playlist_title: str,
        use_id3: bool = True,
        use_covers: bool = True,
    ):
        if not use_id3:
            return True

        try:
            logger.debug(f"Открытие файла для тегирования: {filepath}")
            audio = MP3(filepath, ID3=ID3)
            try:
                audio.add_tags()
                logger.debug(f"Добавлены новые ID3 теги для {filepath}")
            except:
                logger.debug(f"ID3 теги уже существуют в {filepath}")
                pass

            # 1. Text
            title_text = track.title
            if track.subtitle:
                title_text += f" ({track.subtitle})"
            logger.debug(f"Установка заголовка: {title_text}")
            audio.tags.add(TIT2(encoding=3, text=title_text))

            # Artists
            artists = []
            if track.main_artists:
                artists = [m["name"] for m in track.main_artists]
            else:
                artists = [track.artist]

            if track.feat_artists:
                feat = [f["name"] for f in track.feat_artists]
                artists += feat

            audio.tags.add(TPE1(encoding=3, text=artists))
            audio.tags.add(TPE2(encoding=3, text=", ".join(artists)))

            # 2. Duration / Date
            audio.tags.add(TLEN(encoding=3, text=str(int(track.duration * 1000))))
            if track.date:
                full_date = datetime.fromtimestamp(track.date).strftime("%Y-%m-%d")
                audio.tags.add(TDRC(encoding=3, text=full_date))

            # 3. Album
            album = track.album_obj
            if album and track.source != "yandex":
                audio.tags.add(TALB(encoding=3, text=album["title"]))
                # WOAS
                alb_url = (
                    f"https://vk.com/music/album/{album['owner_id']}_{album['id']}"
                )
                if album.get("access_key"):
                    alb_url += f"_{album['access_key']}"
                audio.tags.add(WOAS(url=alb_url))
            else:
                audio.tags.add(TALB(encoding=3, text=playlist_title))

            # 4. URLs
            if track.source == "yandex":
                # Yandex Music URL
                if track.url:
                    audio.tags.add(WOAF(url=track.url))
            else:
                # VK-specific URLs
                if track.main_artists:
                    main_art = track.main_artists[0]
                    art_id = main_art.get("domain") or main_art.get("id")
                    if art_id:
                        audio.tags.add(WOAR(url=f"https://vk.com/artist/{art_id}"))

                audio.tags.add(WOAF(url=f"https://vk.com/audio{track.id}"))

            # 5. Genre
            if track.genre_id and track.genre_id in VK_GENRES:
                audio.tags.add(TCON(encoding=3, text=VK_GENRES[track.genre_id]))

            # 6. Comment
            audio.tags.add(
                COMM(
                    encoding=3,
                    lang="rus",
                    desc="vknext.net",
                    text=["BK Music Saver Pro"],
                )
            )

            # 7. Cover
            if use_covers and track.cover_url:
                logger.debug(f"Загрузка обложки для {track.id} из {track.cover_url}")
                try:
                    r = requests.get(track.cover_url, timeout=10)
                    if r.status_code == 200:
                        img_data = r.content
                        mime = (
                            "image/png"
                            if img_data.startswith(b"\x89PNG")
                            else "image/jpeg"
                        )
                        logger.debug(
                            f"Обложка получена успешно (MIME: {mime}, размер: {len(img_data)} байт)"
                        )
                        audio.tags.add(
                            APIC(
                                encoding=3,
                                mime=mime,
                                type=3,
                                desc="Cover",
                                data=img_data,
                            )
                        )
                    else:
                        logger.warning(
                            f"Сервер вернул статус {r.status_code} при загрузке обложки."
                        )
                except Exception as e:
                    logger.warning(f"Ошибка при загрузке обложки: {e}")

            logger.debug(f"Сохранение изменений ID3 в файл: {filepath}")
            audio.save(v2_version=3)
            logger.info(f"Тегирование завершено успешно: {filepath}")
            return True
        except Exception as e:
            logger.error(f"Критическая ошибка Tagger для {filepath}: {e}")
            return False


def sanitize_filename(name):
    return re.sub(r'[\\/*?:"<>|]', "", name).strip()
