import os
import time

import requests

from src.utils.logger import logger


class SimpleHTTPDownloadError(Exception):
    pass


class SimpleHTTPDownloadService:
    @staticmethod
    def _detect_payload_kind(head: bytes) -> str:
        if not head:
            return "empty"
        lower = head.lower()
        if b"<html" in lower or b"<!doctype html" in lower:
            return "html"
        if head.startswith(b"ID3"):
            return "mp3_id3"
        if len(head) >= 2 and head[0] == 0xFF and (head[1] & 0xE0) == 0xE0:
            return "mpeg_frame"
        if b"ftyp" in head[:64]:
            return "mp4_or_m4a"
        if head.startswith(b"OggS"):
            return "ogg"
        if head.startswith(b"RIFF"):
            return "wav_or_riff"
        if b"showcaptcha" in lower:
            return "captcha_text"
        return "unknown_binary"

    @staticmethod
    def download(url: str, filepath: str, timeout: int = 45, headers: dict = None):
        if not url or not url.startswith("http"):
            raise SimpleHTTPDownloadError("Invalid direct URL")

        logger.info(
            f"[HTTP_DL_START] url={url[:120]} filepath={filepath} timeout={timeout}s"
        )
        os.makedirs(os.path.dirname(filepath), exist_ok=True)

        started = time.time()
        written_bytes = 0
        chunks_count = 0

        try:
            with requests.get(
                url, stream=True, timeout=timeout, headers=headers or {}
            ) as response:
                content_type = str(response.headers.get("Content-Type") or "").lower()
                final_url = str(response.url or "")
                final_url_lower = final_url.lower()
                logger.debug(
                    "[HTTP_DL_RESPONSE] "
                    f"status={response.status_code} content_type={response.headers.get('Content-Type')} "
                    f"content_length={response.headers.get('Content-Length')} final_url={final_url}"
                )
                if response.history:
                    redirects = " -> ".join(
                        [str(r.status_code) for r in response.history]
                        + [str(response.status_code)]
                    )
                    logger.info(f"[HTTP_DL_RESPONSE] redirects={redirects}")
                response.raise_for_status()

                if "showcaptcha" in final_url_lower or "text/html" in content_type:
                    logger.warning(
                        "[HTTP_DL_FAIL] reason=html_or_captcha_response "
                        f"content_type={content_type} final_url={final_url}"
                    )
                    raise SimpleHTTPDownloadError(
                        "Server returned CAPTCHA/HTML page instead of audio stream"
                    )

                with open(filepath, "wb") as file_obj:
                    for chunk in response.iter_content(chunk_size=64 * 1024):
                        if chunk:
                            file_obj.write(chunk)
                            written_bytes += len(chunk)
                            chunks_count += 1
        except requests.RequestException as exc:
            status_code = getattr(getattr(exc, "response", None), "status_code", None)
            logger.warning(
                f"[HTTP_DL_FAIL] reason=request_exception type={type(exc).__name__} "
                f"status={status_code} error={exc} url={url[:120]}"
            )
            raise SimpleHTTPDownloadError(
                f"HTTP download failed: {type(exc).__name__}, status={status_code}, details={exc}"
            ) from exc
        except Exception as exc:
            logger.exception(f"[HTTP_DL_FAIL] reason=unexpected error={exc}")
            raise SimpleHTTPDownloadError(f"Unexpected download error: {exc}") from exc

        file_size = os.path.getsize(filepath) if os.path.exists(filepath) else 0
        elapsed = round(time.time() - started, 2)
        logger.info(
            f"[HTTP_DL_END] written_bytes={written_bytes} chunks={chunks_count} "
            f"file_size={file_size} elapsed={elapsed}s"
        )

        if not os.path.exists(filepath) or file_size <= 1024:
            logger.warning(
                f"[HTTP_DL_FAIL] reason=small_or_missing_file file_exists={os.path.exists(filepath)} size={file_size}"
            )
            raise SimpleHTTPDownloadError(
                f"Downloaded file is empty or too small: size={file_size} bytes"
            )

        try:
            with open(filepath, "rb") as file_obj:
                head_raw = file_obj.read(4096)
            payload_kind = SimpleHTTPDownloadService._detect_payload_kind(head_raw)
            logger.info(
                f"[HTTP_DL_VALIDATE] payload_kind={payload_kind} head_hex={head_raw[:16].hex()}"
            )
            head = head_raw.lower()
            if b"<html" in head or b"<!doctype html" in head or b"showcaptcha" in head:
                try:
                    os.remove(filepath)
                except Exception:
                    pass
                logger.warning("[HTTP_DL_FAIL] reason=html_payload_detected_in_file")
                raise SimpleHTTPDownloadError(
                    "Downloaded payload is HTML/CAPTCHA, not audio"
                )
        except SimpleHTTPDownloadError:
            raise
        except Exception as exc:
            logger.warning(f"[HTTP_DL_FAIL] reason=file_validation_error error={exc}")
            raise SimpleHTTPDownloadError(f"File validation failed: {exc}") from exc
