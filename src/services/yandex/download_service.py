import os
from typing import Optional

from src.utils.logger import logger


class YandexDownloadService:
    """Downloads tracks from Yandex Music using the yandex-music library."""

    def __init__(self, token: str):
        self.token = token
        self.client = None
        self._init_client()

    def _init_client(self):
        if not self.token:
            logger.warning("YandexDownloadService: no token provided")
            return

        try:
            from yandex_music import Client

            self.client = Client(self.token).init()
            logger.info("YandexDownloadService: client initialized successfully")
        except ImportError:
            logger.error(
                "yandex-music library not installed. Run: pip install yandex-music"
            )
            self.client = None
        except Exception as e:
            logger.error(f"YandexDownloadService init error: {e}")
            self.client = None

    def is_available(self) -> bool:
        return self.client is not None

    def download_track(
        self,
        track_id: str,
        album_id: str,
        filepath: str,
        codec: str = "mp3",
        bitrate: int = 320,
    ) -> bool:
        """Download a single track by its Yandex Music IDs.

        Args:
            track_id: Yandex Music track ID (e.g. "104074051").
            album_id: Yandex Music album ID (e.g. "22400827").
            filepath: Destination file path.
            codec: Audio codec — ``mp3`` (default) or ``aac``.
            bitrate: Desired bitrate in kbps (default 320).

        Returns:
            ``True`` if the file was downloaded successfully.
        """
        if not self.client:
            logger.error("YandexDownloadService: client not available")
            return False

        try:
            track_key = f"{track_id}:{album_id}" if album_id else str(track_id)
            logger.info(f"YandexDownload: fetching track {track_key}")

            tracks = self.client.tracks([track_key])
            if not tracks:
                logger.warning(f"YandexDownload: track {track_key} not found via API")
                return False

            track = tracks[0]
            logger.info(
                f"YandexDownload: downloading '{track.title}' by "
                f"{', '.join(a.name for a in (track.artists or []))} -> {filepath}"
            )
            track.download(filepath, codec=codec, bitrate_in_kbps=bitrate)

            if os.path.exists(filepath) and os.path.getsize(filepath) > 1024:
                logger.info(
                    f"YandexDownload: success ({os.path.getsize(filepath)} bytes)"
                )
                return True

            logger.warning("YandexDownload: downloaded file is missing or too small")
            return False

        except Exception as e:
            logger.error(f"YandexDownload: error downloading track {track_id}: {e}")
            return False

    @staticmethod
    def extract_ids_from_track_id(ym_track_id: str) -> tuple:
        """Parse ``ym_{track_id}_{album_id}`` format into ``(track_id, album_id)``."""
        parts = ym_track_id.split("_")
        # Expected: ["ym", "<track_id>", "<album_id>"]
        track_id = parts[1] if len(parts) > 1 else ""
        album_id = parts[2] if len(parts) > 2 else ""
        if album_id == "0":
            album_id = ""
        return track_id, album_id
