import os
import subprocess
from src.config import FFMPEG_PATH, DOWNLOAD_DIR
from src.utils.logger import logger

class DownloadError(Exception):
    pass


class FFmpegService:
    @staticmethod
    def download(url: str, filepath: str):
        logger.debug(f"FFmpegService: Start download -> {filepath}")
        cmd = [
            FFMPEG_PATH,
            "-y",
            "-hide_banner",
            "-loglevel",
            "error",
            "-i",
            url,
            "-codec:a",
            "libmp3lame",
            "-b:a",
            "320k",
            "-ar",
            "44100",
            filepath,
        ]

        try:
            subprocess.run(
                cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, check=True
            )
            if not os.path.exists(filepath):
                raise DownloadError("File was not created by ffmpeg")
        except subprocess.CalledProcessError as e:
            raise DownloadError(f"FFmpeg failed with return code {e.returncode}")
        except Exception as e:
            raise DownloadError(f"Unexpected error: {e}")
