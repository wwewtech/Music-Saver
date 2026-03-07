import os
import shutil
import subprocess
import sys
import tempfile
import time
import uuid
from typing import Optional

from src.config import FFMPEG_PATH
from src.utils.logger import logger


class DownloadError(Exception):
    pass


class FFmpegService:
    # ── Helpers for non-ASCII path safety on Windows ─────────────────
    # FFmpeg on Windows uses main() (ANSI codepage) instead of wmain(),
    # so Cyrillic and other non-ASCII characters in file paths get
    # corrupted when passed via subprocess.  Workaround: redirect
    # FFmpeg I/O through a temp directory with an ASCII-only path.

    @staticmethod
    def _has_non_ascii(path: str) -> bool:
        try:
            path.encode("ascii")
            return False
        except (UnicodeEncodeError, UnicodeDecodeError):
            return True

    @staticmethod
    def _make_safe_temp_dir() -> str:
        return tempfile.mkdtemp(prefix="ffmpeg_")

    @staticmethod
    def download(url: str, filepath: str, headers: Optional[dict[str, str]] = None):
        if not os.path.exists(FFMPEG_PATH):
            raise DownloadError(f"FFmpeg binary not found: {FFMPEG_PATH}")
        if not url or not url.startswith("http"):
            raise DownloadError("Invalid URL for ffmpeg download")

        # ── Safe-path wrapper ────────────────────────────────────────
        _temp_dir = None
        _final_filepath = filepath
        if sys.platform == "win32" and FFmpegService._has_non_ascii(filepath):
            _temp_dir = FFmpegService._make_safe_temp_dir()
            ext = os.path.splitext(filepath)[1] or ".mp3"
            filepath = os.path.join(_temp_dir, f"dl_{uuid.uuid4().hex[:8]}{ext}")
            logger.info(f"[FFMPEG_DL_SAFE_PATH] non-ASCII detected, temp={filepath}")

        logger.info(
            f"[FFMPEG_DL_START] ffmpeg={FFMPEG_PATH} url={url[:120]} filepath={_final_filepath}"
        )

        try:
            cmd = [
                FFMPEG_PATH,
                "-y",
                "-hide_banner",
                "-loglevel",
                "error",
            ]

            if headers:
                header_lines = [
                    f"{key}: {value}" for key, value in headers.items() if value
                ]
                if header_lines:
                    headers_blob = "\r\n".join(header_lines) + "\r\n"
                    cmd += ["-headers", headers_blob]
                    logger.info(
                        f"[FFMPEG_DL_HEADERS] count={len(header_lines)} "
                        f"keys={[line.split(':', 1)[0] for line in header_lines]} "
                        f"blob_len={len(headers_blob)}"
                    )

            cmd += [
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

            logger.debug(f"[FFMPEG_DL_CMD] cmd_preview={' '.join(cmd[:12])} ...")

            started = time.time()
            try:
                result = subprocess.run(
                    cmd,
                    capture_output=True,
                    text=True,
                    check=True,
                    timeout=300,
                )
                if not os.path.exists(filepath):
                    raise DownloadError("File was not created by ffmpeg")
                file_size = os.path.getsize(filepath)
                logger.info(
                    f"[FFMPEG_DL_END] returncode={result.returncode} file_size={file_size} "
                    f"elapsed={round(time.time() - started, 2)}s"
                )
            except subprocess.CalledProcessError as e:
                stderr_text = (e.stderr or "").strip().replace("\n", " | ")
                logger.warning(
                    f"[FFMPEG_DL_FAIL] reason=called_process_error code={e.returncode} "
                    f"stderr={stderr_text[:500]}"
                )
                raise DownloadError(
                    f"FFmpeg failed with return code {e.returncode}. stderr={stderr_text[:300]}"
                )
            except subprocess.TimeoutExpired as e:
                logger.warning(f"[FFMPEG_DL_FAIL] reason=timeout seconds={e.timeout}")
                raise DownloadError(f"FFmpeg timeout after {e.timeout} seconds")
            except Exception as e:
                logger.exception(f"[FFMPEG_DL_FAIL] reason=unexpected error={e}")
                raise DownloadError(f"Unexpected error: {e}")

            # Move from temp to final destination
            if _temp_dir and filepath != _final_filepath and os.path.exists(filepath):
                os.makedirs(os.path.dirname(_final_filepath), exist_ok=True)
                shutil.move(filepath, _final_filepath)
                logger.debug(f"[FFMPEG_DL_SAFE_PATH] moved to {_final_filepath}")
        finally:
            if _temp_dir:
                shutil.rmtree(_temp_dir, ignore_errors=True)

    @staticmethod
    def transcode_to_mp3(input_path: str, output_path: str):
        if not os.path.exists(FFMPEG_PATH):
            raise DownloadError(f"FFmpeg binary not found: {FFMPEG_PATH}")
        if not os.path.exists(input_path):
            raise DownloadError(f"Input file for transcode not found: {input_path}")

        # ── Safe-path wrapper ────────────────────────────────────────
        _temp_dir = None
        _final_output = output_path
        if sys.platform == "win32" and (
            FFmpegService._has_non_ascii(input_path)
            or FFmpegService._has_non_ascii(output_path)
        ):
            _temp_dir = FFmpegService._make_safe_temp_dir()
            if FFmpegService._has_non_ascii(input_path):
                in_ext = os.path.splitext(input_path)[1] or ".source"
                safe_input = os.path.join(
                    _temp_dir, f"in_{uuid.uuid4().hex[:8]}{in_ext}"
                )
                shutil.copy2(input_path, safe_input)
                input_path = safe_input
                logger.info(f"[FFMPEG_TRANSCODE_SAFE_PATH] input temp={safe_input}")
            if FFmpegService._has_non_ascii(output_path):
                out_ext = os.path.splitext(output_path)[1] or ".mp3"
                output_path = os.path.join(
                    _temp_dir, f"out_{uuid.uuid4().hex[:8]}{out_ext}"
                )
                logger.info(f"[FFMPEG_TRANSCODE_SAFE_PATH] output temp={output_path}")

        logger.info(
            f"[FFMPEG_TRANSCODE_START] ffmpeg={FFMPEG_PATH} input={input_path} output={output_path}"
        )

        try:
            cmd = [
                FFMPEG_PATH,
                "-y",
                "-hide_banner",
                "-loglevel",
                "error",
                "-i",
                input_path,
                "-codec:a",
                "libmp3lame",
                "-b:a",
                "320k",
                "-ar",
                "44100",
                output_path,
            ]

            logger.debug(f"[FFMPEG_TRANSCODE_CMD] cmd_preview={' '.join(cmd[:10])} ...")

            started = time.time()
            try:
                result = subprocess.run(
                    cmd,
                    capture_output=True,
                    text=True,
                    check=True,
                    timeout=300,
                )
                if not os.path.exists(output_path):
                    raise DownloadError(
                        "Output file was not created by ffmpeg transcode"
                    )
                file_size = os.path.getsize(output_path)
                logger.info(
                    f"[FFMPEG_TRANSCODE_END] returncode={result.returncode} file_size={file_size} "
                    f"elapsed={round(time.time() - started, 2)}s"
                )
            except subprocess.CalledProcessError as e:
                stderr_text = (e.stderr or "").strip().replace("\n", " | ")
                logger.warning(
                    f"[FFMPEG_TRANSCODE_FAIL] reason=called_process_error code={e.returncode} "
                    f"stderr={stderr_text[:500]}"
                )
                raise DownloadError(
                    f"FFmpeg transcode failed with return code {e.returncode}. "
                    f"stderr={stderr_text[:300]}"
                )
            except subprocess.TimeoutExpired as e:
                logger.warning(
                    f"[FFMPEG_TRANSCODE_FAIL] reason=timeout seconds={e.timeout}"
                )
                raise DownloadError(
                    f"FFmpeg transcode timeout after {e.timeout} seconds"
                )
            except Exception as e:
                logger.exception(f"[FFMPEG_TRANSCODE_FAIL] reason=unexpected error={e}")
                raise DownloadError(f"Unexpected transcode error: {e}")

            # Move from temp to final destination
            if (
                _temp_dir
                and output_path != _final_output
                and os.path.exists(output_path)
            ):
                os.makedirs(os.path.dirname(_final_output), exist_ok=True)
                shutil.move(output_path, _final_output)
                logger.debug(f"[FFMPEG_TRANSCODE_SAFE_PATH] moved to {_final_output}")
        finally:
            if _temp_dir:
                shutil.rmtree(_temp_dir, ignore_errors=True)
