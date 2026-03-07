"""
Auto-download of required third-party binaries (ffmpeg).

Chromedriver is NOT managed here — Selenium Manager (built into
selenium ≥ 4.10) handles it automatically.

FFmpeg is downloaded from the official BtbN GitHub Releases page
(https://github.com/BtbN/FFmpeg-Builds/releases) on first launch.
"""

import io
import os
import platform
import shutil
import stat
import sys
import zipfile
from typing import Optional

import requests

from src.utils.logger import logger

# ── FFmpeg source URLs by platform ──────────────────────────────────────
# essentials builds — small, contains only ffmpeg/ffprobe, ~30 MB zip
_FFMPEG_URLS: dict[str, str] = {
    "win64": (
        "https://github.com/BtbN/FFmpeg-Builds/releases/download/"
        "latest/ffmpeg-master-latest-win64-gpl.zip"
    ),
    "linux64": (
        "https://github.com/BtbN/FFmpeg-Builds/releases/download/"
        "latest/ffmpeg-master-latest-linux64-gpl.tar.xz"
    ),
}

_DOWNLOAD_TIMEOUT = 120  # seconds


def _platform_key() -> str:
    """Return a short key describing current OS + arch."""
    is_64 = sys.maxsize > 2**32
    if sys.platform == "win32":
        return "win64" if is_64 else "win32"
    if sys.platform.startswith("linux"):
        return "linux64" if is_64 else "linux32"
    if sys.platform == "darwin":
        return "macos"
    return "unknown"


class BinaryManager:
    """Downloads and caches required binaries into *bin_dir*."""

    def __init__(self, bin_dir: str):
        self.bin_dir = bin_dir
        os.makedirs(self.bin_dir, exist_ok=True)

    # ── Public API ──────────────────────────────────────────────────

    def ensure_ffmpeg(self) -> str:
        """Return path to ffmpeg executable; download if missing.

        Raises ``RuntimeError`` if the binary cannot be obtained.
        """
        ffmpeg_name = "ffmpeg.exe" if sys.platform == "win32" else "ffmpeg"
        ffmpeg_path = os.path.join(self.bin_dir, ffmpeg_name)

        if os.path.isfile(ffmpeg_path):
            logger.debug(f"FFmpeg already exists: {ffmpeg_path}")
            return ffmpeg_path

        # Try system-wide ffmpeg first
        system_ffmpeg = shutil.which("ffmpeg")
        if system_ffmpeg:
            logger.info(f"Using system FFmpeg: {system_ffmpeg}")
            return system_ffmpeg

        # Download
        pk = _platform_key()
        url = _FFMPEG_URLS.get(pk)
        if not url:
            raise RuntimeError(
                f"Automatic FFmpeg download is not supported on {pk}. "
                f"Please install FFmpeg manually and place it in: {self.bin_dir}"
            )

        logger.info(f"Downloading FFmpeg for {pk} from {url} ...")
        self._download_ffmpeg(url, ffmpeg_path)
        return ffmpeg_path

    # ── Internals ───────────────────────────────────────────────────

    def _download_ffmpeg(self, url: str, dest: str) -> None:
        """Download and extract ffmpeg binary from *url* to *dest*."""
        try:
            resp = requests.get(url, stream=True, timeout=_DOWNLOAD_TIMEOUT)
            resp.raise_for_status()
        except requests.RequestException as exc:
            raise RuntimeError(f"Failed to download FFmpeg: {exc}") from exc

        content_bytes = resp.content
        total_mb = round(len(content_bytes) / (1024 * 1024), 1)
        logger.info(f"FFmpeg archive downloaded: {total_mb} MB")

        if url.endswith(".zip"):
            self._extract_from_zip(content_bytes, dest)
        elif url.endswith(".tar.xz"):
            self._extract_from_tar_xz(content_bytes, dest)
        else:
            raise RuntimeError(f"Unknown archive format: {url}")

        if not os.path.isfile(dest):
            raise RuntimeError(
                f"FFmpeg binary was not found in the archive. Expected at: {dest}"
            )

        # Ensure executable permission on Unix
        if sys.platform != "win32":
            os.chmod(dest, os.stat(dest).st_mode | stat.S_IEXEC)

        logger.info(f"FFmpeg installed: {dest}")

    @staticmethod
    def _extract_from_zip(data: bytes, dest: str) -> None:
        """Extract ffmpeg[.exe] from a zip archive."""
        target_name = os.path.basename(dest)  # "ffmpeg.exe" or "ffmpeg"
        dest_dir = os.path.dirname(dest)

        with zipfile.ZipFile(io.BytesIO(data)) as zf:
            for member in zf.namelist():
                basename = os.path.basename(member)
                if basename.lower() == target_name.lower():
                    logger.debug(f"Extracting {member} -> {dest}")
                    with zf.open(member) as src, open(dest, "wb") as dst:
                        shutil.copyfileobj(src, dst)
                    return

        raise RuntimeError(
            f"'{target_name}' not found inside the zip archive"
        )

    @staticmethod
    def _extract_from_tar_xz(data: bytes, dest: str) -> None:
        """Extract ffmpeg from a .tar.xz archive (Linux)."""
        import lzma
        import tarfile

        target_name = os.path.basename(dest)
        with lzma.open(io.BytesIO(data)) as xz:
            with tarfile.open(fileobj=xz) as tf:
                for member in tf.getmembers():
                    basename = os.path.basename(member.name)
                    if basename == target_name and member.isfile():
                        logger.debug(f"Extracting {member.name} -> {dest}")
                        reader = tf.extractfile(member)
                        if reader is None:
                            continue
                        with open(dest, "wb") as dst:
                            shutil.copyfileobj(reader, dst)
                        return

        raise RuntimeError(
            f"'{target_name}' not found inside the tar.xz archive"
        )
