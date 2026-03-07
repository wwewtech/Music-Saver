import os
import time
import tempfile
import json
import re
from copy import deepcopy
from typing import Any
from urllib.parse import urlparse

from mutagen import File as MutagenFile

from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

from src.config import PROFILE_DIR
from src.services.download.ffmpeg_service import FFmpegService, DownloadError
from src.services.download.simple_http_service import (
    SimpleHTTPDownloadService,
    SimpleHTTPDownloadError,
)
from src.utils.logger import logger


class YandexSimpleDownloadService:
    @staticmethod
    def _classify_media_url(url: str) -> str:
        lurl = str(url or "").lower()
        if "showcaptcha" in lurl:
            return "captcha"
        if "get-file-info/batch" in lurl:
            return "api_get_file_info_batch"
        if "get-file-info" in lurl:
            return "api_get_file_info"
        if "/plays?" in lurl:
            return "api_plays"
        if ".m3u8" in lurl:
            return "hls_manifest"
        if "get-mp3" in lurl:
            return "direct_get_mp3"
        if ".mp3" in lurl or ".m4a" in lurl or ".aac" in lurl or ".ogg" in lurl:
            return "direct_audio_file"
        if "strm.yandex" in lurl or "media.yandex" in lurl:
            return "yandex_media_host"
        return "unknown"

    @staticmethod
    def _collect_urls_from_json(value: Any, out: list[str]) -> None:
        if isinstance(value, dict):
            for nested in value.values():
                YandexSimpleDownloadService._collect_urls_from_json(nested, out)
            return
        if isinstance(value, list):
            for nested in value:
                YandexSimpleDownloadService._collect_urls_from_json(nested, out)
            return
        if isinstance(value, str) and value.startswith("http"):
            out.append(value)

    @staticmethod
    def _short_url(url: str, limit: int = 180) -> str:
        text = str(url or "")
        if len(text) <= limit:
            return text
        return text[:limit] + "..."

    @staticmethod
    def _log_network_snapshot(browser_driver: Any, limit: int = 12) -> None:
        try:
            perf_logs = browser_driver.get_log("performance")
        except Exception as exc:
            logger.debug(f"[YM_BROWSER_DL] snapshot_unavailable error={exc}")
            return

        rows: list[str] = []
        for item in perf_logs[-300:]:
            try:
                payload = json.loads(item.get("message", "{}"))
                message = payload.get("message", {})
                method = message.get("method", "")
                if method not in (
                    "Network.requestWillBeSent",
                    "Network.responseReceived",
                ):
                    continue

                params = message.get("params", {}) or {}
                if method == "Network.requestWillBeSent":
                    url = str((params.get("request", {}) or {}).get("url", ""))
                    mime = ""
                else:
                    response = params.get("response", {}) or {}
                    url = str(response.get("url", ""))
                    mime = str(response.get("mimeType", "") or "").lower()

                if not url.startswith("http"):
                    continue
                lurl = url.lower()
                if not YandexSimpleDownloadService._is_likely_media_url(lurl) and not (
                    mime and ("audio" in mime or "mpegurl" in mime)
                ):
                    continue

                rows.append(f"{method}|mime={mime or '-'}|url={url[:180]}")
            except Exception:
                continue

        if rows:
            logger.info(f"[YM_BROWSER_DL] network_snapshot count={len(rows)}")
            for row in rows[-limit:]:
                logger.info(f"[YM_BROWSER_DL] network_snapshot_item {row}")
        else:
            logger.info("[YM_BROWSER_DL] network_snapshot empty")

    @staticmethod
    def _try_start_playback(browser_driver: Any) -> bool:
        selectors = [
            "button[aria-label*='Воспроизв']",
            "button[aria-label*='Play']",
            "button[title*='Воспроизв']",
            "button[title*='Play']",
            "button[data-test-id*='play']",
            "button[class*='playButton']",
            "button[class*='PlayButton']",
            "div[role='button'][aria-label*='Воспроизв']",
        ]

        clicked = False
        clicked_selector = ""
        for selector in selectors:
            buttons = browser_driver.find_elements(By.CSS_SELECTOR, selector)
            for button in buttons:
                try:
                    if button.is_displayed() and button.is_enabled():
                        browser_driver.execute_script("arguments[0].click();", button)
                        clicked = True
                        clicked_selector = selector
                        break
                except Exception:
                    continue
            if clicked:
                break

        if clicked:
            logger.info(
                f"[YM_BROWSER_DL] playback_start_click_ok selector={clicked_selector}"
            )
        else:
            logger.warning("[YM_BROWSER_DL] playback_start_click_not_found")

        # Try JS playback from audio element
        js_play_ok = False
        try:
            js_play_ok = bool(
                browser_driver.execute_script(
                    """
                    const audio = document.querySelector('audio');
                    if (!audio) return false;
                    audio.muted = true;
                    audio.volume = 0;
                    const p = audio.play();
                    if (p && typeof p.then === 'function') {
                        return true;
                    }
                    return !audio.paused;
                    """
                )
            )
        except Exception:
            js_play_ok = False

        # Keyboard fallback (often works when focus is on player page)
        key_ok = False
        try:
            body = browser_driver.find_element(By.TAG_NAME, "body")
            body.click()
            body.send_keys(Keys.SPACE)
            time.sleep(0.2)
            body.send_keys("k")
            key_ok = True
        except Exception:
            key_ok = False

        logger.info(
            f"[YM_BROWSER_DL] playback_start_result clicked={clicked} js_play={js_play_ok} keyboard={key_ok}"
        )
        return clicked or js_play_ok or key_ok

    @staticmethod
    def _log_player_state(browser_driver: Any, stage: str) -> None:
        try:
            state = (
                browser_driver.execute_script(
                    """
                const audio = document.querySelector('audio');
                const titleNode = document.querySelector('[class*="d-track__name"] a, [class*="TrackTitle"], h1');
                const playBtn = document.querySelector('button[aria-label*="Воспроизв"], button[aria-label*="Play"], button[class*="playButton"], button[class*="PlayButton"]');
                return {
                    href: location.href,
                    readyState: audio ? audio.readyState : null,
                    networkState: audio ? audio.networkState : null,
                    paused: audio ? audio.paused : null,
                    currentTime: audio ? audio.currentTime : null,
                    duration: audio ? audio.duration : null,
                    currentSrc: audio ? (audio.currentSrc || audio.src || '') : '',
                    titleText: titleNode ? (titleNode.textContent || '').trim() : '',
                    playBtnAria: playBtn ? (playBtn.getAttribute('aria-label') || '') : '',
                    playBtnTitle: playBtn ? (playBtn.getAttribute('title') || '') : '',
                };
                """
                )
                or {}
            )
            logger.info(
                "[YM_BROWSER_DL][player_state] "
                f"stage={stage} href={YandexSimpleDownloadService._short_url(state.get('href', ''))} "
                f"title='{(state.get('titleText') or '')[:80]}' paused={state.get('paused')} readyState={state.get('readyState')} "
                f"networkState={state.get('networkState')} currentTime={state.get('currentTime')} duration={state.get('duration')} "
                f"currentSrc={YandexSimpleDownloadService._short_url(state.get('currentSrc', ''))} "
                f"playBtnAria='{(state.get('playBtnAria') or '')[:40]}' playBtnTitle='{(state.get('playBtnTitle') or '')[:40]}'"
            )
        except Exception as exc:
            logger.debug(
                f"[YM_BROWSER_DL][player_state] stage={stage} unavailable error={exc}"
            )

    @staticmethod
    def _build_cookie_header(browser_driver: Any) -> str:
        if not browser_driver:
            logger.debug("[YM_BROWSER_DL][cookies] no browser driver")
            return ""
        try:
            cookies = browser_driver.get_cookies() or []
        except Exception:
            logger.debug("[YM_BROWSER_DL][cookies] failed to read cookies from driver")
            return ""

        pairs = []
        for cookie in cookies:
            domain = str(cookie.get("domain") or "").lower()
            if "yandex" not in domain:
                continue
            name = str(cookie.get("name") or "").strip()
            value = str(cookie.get("value") or "")
            if name:
                pairs.append(f"{name}={value}")
        logger.info(
            f"[YM_BROWSER_DL][cookies] total={len(cookies)} yandex_pairs={len(pairs)} header_len={len('; '.join(pairs))}"
        )
        return "; ".join(pairs)

    @staticmethod
    def _extract_direct_audio_from_get_file_info_body(body: str) -> str:
        if not body:
            return ""

        normalized_body = (
            body.replace("\\/", "/")
            .replace("\\u002F", "/")
            .replace("\\u003A", ":")
            .replace("\\u0026", "&")
        )

        json_candidates: list[str] = []
        try:
            parsed = json.loads(normalized_body)
            if isinstance(parsed, dict):
                logger.debug(
                    "[YM_BROWSER_DL][get_file_info] "
                    f"json_top_keys={list(parsed.keys())[:12]}"
                )
            YandexSimpleDownloadService._collect_urls_from_json(parsed, json_candidates)
            logger.debug(
                f"[YM_BROWSER_DL][get_file_info] json_url_candidates={len(json_candidates)}"
            )
        except Exception:
            logger.debug(
                "[YM_BROWSER_DL][get_file_info] body is not JSON or JSON parse failed"
            )

        if json_candidates:
            for idx, url in enumerate(json_candidates[:5], start=1):
                logger.debug(
                    "[YM_BROWSER_DL][get_file_info] "
                    f"json_candidate_{idx} class={YandexSimpleDownloadService._classify_media_url(url)} "
                    f"url={YandexSimpleDownloadService._short_url(url)}"
                )

        for url in json_candidates:
            lurl = url.lower()
            if "showcaptcha" in lurl:
                continue
            if any(
                marker in lurl
                for marker in [
                    ".m3u8",
                    "get-mp3",
                    ".mp3",
                    ".m4a",
                    "download",
                    "audio",
                    "stream",
                    "strm.yandex",
                    "media.yandex",
                ]
            ):
                return url

        candidates = re.findall(r"https?://[^\"'\\\s]+", normalized_body)
        if candidates:
            logger.debug(
                f"[YM_BROWSER_DL][get_file_info] regex_url_candidates={len(candidates)}"
            )
            for idx, url in enumerate(candidates[:5], start=1):
                logger.debug(
                    "[YM_BROWSER_DL][get_file_info] "
                    f"regex_candidate_{idx} class={YandexSimpleDownloadService._classify_media_url(url)} "
                    f"url={YandexSimpleDownloadService._short_url(url)}"
                )
        for url in candidates:
            lurl = url.lower()
            if "showcaptcha" in lurl:
                continue
            if any(
                marker in lurl
                for marker in [
                    ".m3u8",
                    "get-mp3",
                    ".mp3",
                    ".m4a",
                    "download",
                    "audio",
                    "stream",
                ]
            ):
                return url
        return ""

    @staticmethod
    def _is_captcha_error(exc: Exception) -> bool:
        text = str(exc).lower()
        return (
            "captcha" in text
            or "showcaptcha" in text
            or "403 forbidden" in text
            or "access denied" in text
        )

    @staticmethod
    def _open_and_wait_captcha_resolution(browser_driver: Any, probe_url: str) -> bool:
        if not browser_driver:
            return False

        try:
            logger.warning(
                f"[YM_BROWSER_DL][captcha] opening challenge page url={YandexSimpleDownloadService._short_url(probe_url)}"
            )
            browser_driver.get(probe_url)
            WebDriverWait(browser_driver, 15).until(
                EC.presence_of_element_located((By.CSS_SELECTOR, "body"))
            )
        except Exception as exc:
            logger.warning(
                f"[YM_BROWSER_DL][captcha] failed_to_open_challenge error={exc}"
            )
            return False

        wait_seconds = 120
        started = time.time()
        last_log_second = -1
        while time.time() - started < wait_seconds:
            current_url = ""
            title = ""
            try:
                current_url = str(browser_driver.current_url or "")
                title = str(browser_driver.title or "")
            except Exception:
                pass

            lurl = current_url.lower()
            ltitle = title.lower()
            on_captcha = "showcaptcha" in lurl or "captcha" in lurl or "капча" in ltitle

            elapsed = int(time.time() - started)
            if elapsed % 10 == 0 and elapsed != last_log_second:
                last_log_second = elapsed
                logger.info(
                    "[YM_BROWSER_DL][captcha] "
                    f"waiting elapsed={elapsed}s url={YandexSimpleDownloadService._short_url(current_url)}"
                )

            if not on_captcha:
                logger.info(
                    "[YM_BROWSER_DL][captcha] "
                    f"resolved elapsed={elapsed}s url={YandexSimpleDownloadService._short_url(current_url)}"
                )
                return True

            time.sleep(1.0)

        logger.warning(
            "[YM_BROWSER_DL][captcha] timeout while waiting for manual solve"
        )
        return False

    @staticmethod
    def _extract_media_url_via_get_file_info(browser_driver: Any) -> str:
        try:
            perf_logs = browser_driver.get_log("performance")
        except Exception:
            logger.debug("[YM_BROWSER_DL][get_file_info] performance logs unavailable")
            return ""

        logger.debug(f"[YM_BROWSER_DL][get_file_info] perf_logs_count={len(perf_logs)}")
        request_ids: list[str] = []
        seen_get_file_info_urls = 0
        for item in perf_logs:
            try:
                payload = json.loads(item.get("message", "{}"))
                message = payload.get("message", {})
                if message.get("method") != "Network.responseReceived":
                    continue
                params = message.get("params", {})
                response = params.get("response", {}) or {}
                url = str(response.get("url", "")).lower()
                if "get-file-info" in url and "api.music.yandex" in url:
                    seen_get_file_info_urls += 1
                    rid = params.get("requestId")
                    if rid:
                        logger.debug(
                            "[YM_BROWSER_DL][get_file_info] "
                            f"matched_response request_id={rid} url={YandexSimpleDownloadService._short_url(url)}"
                        )
                        request_ids.append(rid)
            except Exception:
                continue

        logger.debug(
            "[YM_BROWSER_DL][get_file_info] "
            f"responses_matched={seen_get_file_info_urls} request_ids={len(request_ids)}"
        )

        for request_id in reversed(request_ids[-15:]):
            try:
                body_obj = browser_driver.execute_cdp_cmd(
                    "Network.getResponseBody", {"requestId": request_id}
                )
                body = str((body_obj or {}).get("body") or "")
                logger.debug(
                    "[YM_BROWSER_DL][get_file_info] "
                    f"request_id={request_id} body_len={len(body)}"
                )
                direct = YandexSimpleDownloadService._extract_direct_audio_from_get_file_info_body(
                    body
                )
                if direct:
                    logger.info(
                        "[YM_BROWSER_DL][get_file_info] "
                        f"direct_audio_found request_id={request_id} url={YandexSimpleDownloadService._short_url(direct)}"
                    )
                    return direct
            except Exception:
                continue

        logger.debug("[YM_BROWSER_DL][get_file_info] no direct url found")

        return ""

    @staticmethod
    def _is_valid_audio_file(filepath: str) -> bool:
        if not os.path.exists(filepath):
            logger.warning(f"[YM_BROWSER_DL][validate] missing file={filepath}")
            return False

        file_size = os.path.getsize(filepath)
        if file_size < 8 * 1024:
            logger.warning(
                f"[YM_BROWSER_DL][validate] too_small size={file_size} file={filepath}"
            )
            return False

        try:
            with open(filepath, "rb") as file_obj:
                head = file_obj.read(2048)
            head_lower = head.lower()
            logger.info(
                "[YM_BROWSER_DL][validate] "
                f"head_hex={head[:16].hex()} contains_ftyp={b'ftyp' in head[:64]} contains_id3={head.startswith(b'ID3')}"
            )
            if b"<html" in head_lower or b"showcaptcha" in head_lower:
                logger.warning(
                    f"[YM_BROWSER_DL][validate] html_or_captcha_payload file={filepath} size={file_size}"
                )
                return False
        except Exception:
            logger.warning(
                f"[YM_BROWSER_DL][validate] failed to read head file={filepath}"
            )
            return False

        try:
            audio = MutagenFile(filepath)
            if audio and getattr(audio, "info", None):
                duration = float(getattr(audio.info, "length", 0.0) or 0.0)
                if duration > 1.0:
                    logger.info(
                        f"[YM_BROWSER_DL][validate] ok file={filepath} size={file_size} duration={round(duration, 2)}"
                    )
                    return True
        except Exception as exc:
            logger.warning(
                "[YM_BROWSER_DL][validate] "
                f"mutagen_failed file={filepath} error_type={type(exc).__name__} error={exc}"
            )
            return False

        logger.warning(
            f"[YM_BROWSER_DL][validate] no_audio_info file={filepath} size={file_size}"
        )
        return False

    @staticmethod
    def _is_direct_audio_url(url: str) -> bool:
        lurl = str(url).lower()
        if not lurl.startswith("http"):
            return False
        if YandexSimpleDownloadService._is_blocked_analytics_url(lurl):
            return False
        if "showcaptcha" in lurl:
            return False
        if "api.music.yandex.ru/plays" in lurl:
            return False
        if "api.music.yandex.ru/get-file-info" in lurl:
            return False

        direct_markers = [".m3u8", ".mp3", ".m4a", "get-mp3", "playlist.m3u8"]
        return any(marker in lurl for marker in direct_markers)

    @staticmethod
    def _is_blocked_analytics_url(url: str) -> bool:
        lurl = url.lower()
        blocked_markers = [
            "mc.yandex.ru/watch",
            "metrika",
            "log.strm.yandex.ru/log",
            "event=canplay",
            "event=play",
            "event=pause",
            "event=buffer",
            "favicon",
            "/icons/",
            ".css",
            ".js",
            ".svg",
            ".png",
            ".jpg",
            ".jpeg",
            ".webp",
            ".gif",
            ".woff",
        ]
        return any(marker in lurl for marker in blocked_markers)

    @staticmethod
    def _is_likely_media_url(url: str) -> bool:
        lurl = url.lower()
        if YandexSimpleDownloadService._is_blocked_analytics_url(lurl):
            return False
        if "showcaptcha" in lurl:
            return False
        if lurl.startswith("blob:"):
            return False

        media_markers = [
            ".m3u8",
            ".mp3",
            ".m4a",
            "get-mp3",
            "get-file-info",
            "/plays?",
            "audio",
            "playlist.m3u8",
            "download",
            ".ts",
            ".aac",
            ".ogg",
            "stream",
        ]
        if any(marker in lurl for marker in media_markers):
            return True

        media_hosts = [
            "strm.yandex",
            "strm.yandex.net",
            "strm.yandex.ru",
            "media.yandex",
            "storage.yandex",
            "music.yandex",
            "downloader.disk.yandex",
        ]
        return any(host in lurl for host in media_hosts)

    @staticmethod
    def _extract_media_url_from_cdp_response_body(browser_driver: Any) -> str:
        try:
            perf_logs = browser_driver.get_log("performance")
        except Exception:
            logger.debug("[YM_BROWSER_DL][cdp_body] performance logs unavailable")
            return ""

        logger.debug(f"[YM_BROWSER_DL][cdp_body] perf_logs_count={len(perf_logs)}")
        request_ids: list[str] = []
        for item in perf_logs:
            try:
                payload = json.loads(item.get("message", "{}"))
                message = payload.get("message", {})
                if message.get("method") != "Network.responseReceived":
                    continue

                params = message.get("params", {})
                response = params.get("response", {}) or {}
                url = str(response.get("url", ""))
                lurl = url.lower()
                if "music.yandex" not in lurl:
                    continue
                if not any(
                    marker in lurl for marker in ["handlers", "api", "track", "player"]
                ):
                    continue

                request_id = params.get("requestId")
                if request_id:
                    request_ids.append(request_id)
            except Exception:
                continue

        logger.debug(
            f"[YM_BROWSER_DL][cdp_body] candidate_request_ids={len(request_ids)}"
        )

        for request_id in reversed(request_ids[-20:]):
            try:
                body_obj = browser_driver.execute_cdp_cmd(
                    "Network.getResponseBody",
                    {"requestId": request_id},
                )
                body = str((body_obj or {}).get("body") or "")
                if not body:
                    continue

                logger.debug(
                    "[YM_BROWSER_DL][cdp_body] "
                    f"request_id={request_id} body_len={len(body)}"
                )

                matches = re.findall(r"https?://[^\"'\\\s]+", body)
                logger.debug(
                    "[YM_BROWSER_DL][cdp_body] "
                    f"request_id={request_id} url_candidates={len(matches)}"
                )
                for match in matches:
                    if YandexSimpleDownloadService._is_direct_audio_url(match):
                        logger.info(
                            "[YM_BROWSER_DL][cdp_body] "
                            f"direct_audio_found request_id={request_id} url={YandexSimpleDownloadService._short_url(match)}"
                        )
                        return match
            except Exception:
                continue

        logger.debug("[YM_BROWSER_DL][cdp_body] no direct url found")

        return ""

    @staticmethod
    def _extract_media_url_from_resource_entries(browser_driver: Any) -> str:
        try:
            urls = (
                browser_driver.execute_script(
                    """
                const out = [];
                const audio = document.querySelector('audio');
                if (audio) {
                    if (audio.currentSrc) out.push(audio.currentSrc);
                    if (audio.src) out.push(audio.src);
                }
                const entries = performance.getEntriesByType('resource') || [];
                for (const e of entries) {
                    const name = (e && e.name) ? e.name : '';
                    if (name) out.push(name);
                }
                return out;
                """
                )
                or []
            )
        except Exception as exc:
            logger.debug(f"[YM_BROWSER_DL] resource_entries_unavailable error={exc}")
            return ""

        logger.debug(f"[YM_BROWSER_DL][resource_entries] total_entries={len(urls)}")

        filtered: list[str] = []
        skipped_non_str = 0
        skipped_not_media = 0
        for url in urls:
            if not isinstance(url, str):
                skipped_non_str += 1
                continue
            if not YandexSimpleDownloadService._is_likely_media_url(url):
                skipped_not_media += 1
                continue
            filtered.append(url)

        logger.debug(
            "[YM_BROWSER_DL][resource_entries] "
            f"filtered={len(filtered)} skipped_non_str={skipped_non_str} skipped_not_media={skipped_not_media}"
        )

        if not filtered:
            logger.debug("[YM_BROWSER_DL][resource_entries] no media-like entries")
            return ""

        for url in reversed(filtered):
            lurl = url.lower()
            if (
                ".m3u8" in lurl
                or "get-mp3" in lurl
                or ".mp3" in lurl
                or "get-file-info" in lurl
                or "/plays?" in lurl
            ):
                logger.info(
                    "[YM_BROWSER_DL][resource_entries] "
                    f"priority_candidate={YandexSimpleDownloadService._short_url(url)}"
                )
                return url
        logger.info(
            "[YM_BROWSER_DL][resource_entries] "
            f"fallback_candidate={YandexSimpleDownloadService._short_url(filtered[-1])}"
        )
        return filtered[-1]

    @staticmethod
    def _extract_media_url_from_perf_logs(browser_driver: Any) -> str:
        try:
            perf_logs = browser_driver.get_log("performance")
        except Exception as exc:
            logger.warning(f"[YM_BROWSER_DL] failed_to_read_perf_logs error={exc}")
            return ""

        logger.debug(f"[YM_BROWSER_DL][perf_logs] events_count={len(perf_logs)}")
        candidates: list[str] = []
        response_audio_mime_hits = 0
        likely_media_hits = 0

        for item in perf_logs:
            try:
                payload = json.loads(item.get("message", "{}"))
                message = payload.get("message", {})
                method = message.get("method", "")
                params = message.get("params", {})

                if method == "Network.requestWillBeSent":
                    url = (params.get("request", {}) or {}).get("url", "")
                    mime = ""
                elif method == "Network.responseReceived":
                    response = params.get("response", {}) or {}
                    url = response.get("url", "")
                    mime = str(response.get("mimeType", "")).lower()
                    if mime and not (
                        "audio" in mime
                        or "mpegurl" in mime
                        or "application/vnd.apple.mpegurl" in mime
                    ):
                        continue
                else:
                    continue

                lurl = str(url).lower()
                if not lurl.startswith("http"):
                    continue

                if method == "Network.responseReceived" and (
                    "audio" in mime or "mpegurl" in mime
                ):
                    response_audio_mime_hits += 1
                    candidates.append(url)
                    continue

                if YandexSimpleDownloadService._is_likely_media_url(lurl):
                    likely_media_hits += 1
                    candidates.append(url)
            except Exception:
                continue

        logger.debug(
            "[YM_BROWSER_DL][perf_logs] "
            f"candidates={len(candidates)} audio_mime_hits={response_audio_mime_hits} likely_media_hits={likely_media_hits}"
        )

        if not candidates:
            logger.debug("[YM_BROWSER_DL][perf_logs] no candidates")
            return ""

        for url in reversed(candidates):
            lurl = url.lower()
            if (
                ".m3u8" in lurl
                or "get-mp3" in lurl
                or ".mp3" in lurl
                or "get-file-info" in lurl
                or "/plays?" in lurl
            ):
                logger.info(
                    "[YM_BROWSER_DL][perf_logs] "
                    f"priority_candidate={YandexSimpleDownloadService._short_url(url)}"
                )
                return url
        logger.info(
            "[YM_BROWSER_DL][perf_logs] "
            f"fallback_candidate={YandexSimpleDownloadService._short_url(candidates[-1])}"
        )
        return candidates[-1]

    @staticmethod
    def _download_via_browser_playback(
        track_url: str,
        filepath: str,
        browser_driver: Any,
        retried_after_captcha: bool = False,
    ) -> bool:
        if not browser_driver:
            return False

        logger.info(f"[YM_BROWSER_DL] start track_url={track_url}")
        try:
            browser_driver.get(track_url)
            WebDriverWait(browser_driver, 20).until(
                EC.presence_of_element_located((By.CSS_SELECTOR, "body"))
            )
            time.sleep(1.0)
            YandexSimpleDownloadService._log_player_state(browser_driver, "after_open")

            try:
                browser_driver.get_log("performance")
            except Exception:
                pass

            YandexSimpleDownloadService._try_start_playback(browser_driver)
            YandexSimpleDownloadService._log_player_state(
                browser_driver, "after_start_playback"
            )

            media_url = ""
            deadline = time.time() + 20
            rearmed = False
            poll_round = 0
            while time.time() < deadline and not media_url:
                poll_round += 1
                time.sleep(0.8)
                remaining = max(0.0, deadline - time.time())
                logger.debug(
                    f"[YM_BROWSER_DL][poll] round={poll_round} remaining={remaining:.2f}s"
                )

                media_url = (
                    YandexSimpleDownloadService._extract_media_url_via_get_file_info(
                        browser_driver
                    )
                )
                if media_url:
                    logger.info(
                        "[YM_BROWSER_DL][poll] "
                        f"source=get_file_info url={YandexSimpleDownloadService._short_url(media_url)}"
                    )
                    break

                media_url = YandexSimpleDownloadService._extract_media_url_from_resource_entries(
                    browser_driver
                )
                if media_url:
                    logger.info(
                        "[YM_BROWSER_DL][poll] "
                        f"source=resource_entries url={YandexSimpleDownloadService._short_url(media_url)}"
                    )
                    break

                media_url = (
                    YandexSimpleDownloadService._extract_media_url_from_perf_logs(
                        browser_driver
                    )
                )
                if media_url:
                    logger.info(
                        "[YM_BROWSER_DL][poll] "
                        f"source=perf_logs url={YandexSimpleDownloadService._short_url(media_url)}"
                    )
                    break

                media_url = YandexSimpleDownloadService._extract_media_url_from_cdp_response_body(
                    browser_driver
                )
                if media_url:
                    logger.info(
                        "[YM_BROWSER_DL][poll] "
                        f"source=cdp_response_body url={YandexSimpleDownloadService._short_url(media_url)}"
                    )
                    break

                if not media_url and not rearmed and (time.time() + 8) > deadline:
                    rearmed = True
                    logger.info("[YM_BROWSER_DL] rearm_playback_trigger")
                    YandexSimpleDownloadService._try_start_playback(browser_driver)
                    YandexSimpleDownloadService._log_player_state(
                        browser_driver, "after_rearm_playback"
                    )

            if not media_url:
                YandexSimpleDownloadService._log_network_snapshot(browser_driver)
                YandexSimpleDownloadService._log_player_state(
                    browser_driver, "capture_failed"
                )
                logger.warning("[YM_BROWSER_DL] media_url_not_captured")
                return False

            media_class = YandexSimpleDownloadService._classify_media_url(media_url)
            logger.info(f"[YM_BROWSER_DL] media_url_captured prefix={media_url[:140]}")
            logger.info(f"[YM_BROWSER_DL] media_url_class={media_class}")
            if media_class in (
                "api_get_file_info",
                "api_get_file_info_batch",
                "api_plays",
            ):
                logger.warning(
                    "[YM_BROWSER_DL] selected_api_endpoint_not_direct_stream; "
                    "captcha_or_403_is_probable_without browser-solved challenge"
                )

            try:
                cookie_header = YandexSimpleDownloadService._build_cookie_header(
                    browser_driver
                )
                headers = {
                    "User-Agent": (
                        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                        "AppleWebKit/537.36 (KHTML, like Gecko) "
                        "Chrome/145.0.0.0 Safari/537.36"
                    ),
                    "Referer": "https://music.yandex.ru/",
                }
                if cookie_header:
                    headers["Cookie"] = cookie_header

                logger.info(
                    "[YM_BROWSER_DL][download_by_media_url] "
                    f"url={YandexSimpleDownloadService._short_url(media_url)} headers={list(headers.keys())} "
                    f"has_cookie={bool(cookie_header)}"
                )

                if ".m3u8" in media_url.lower() or "get-mp3" in media_url.lower():
                    logger.info(
                        "[YM_BROWSER_DL][download_by_media_url] method=ffmpeg(primary)"
                    )
                    FFmpegService.download(media_url, filepath, headers=headers)
                else:
                    try:
                        logger.info(
                            "[YM_BROWSER_DL][download_by_media_url] method=ffmpeg(first_try)"
                        )
                        FFmpegService.download(media_url, filepath, headers=headers)
                    except DownloadError:
                        media_class = YandexSimpleDownloadService._classify_media_url(
                            media_url
                        )
                        logger.warning(
                            "[YM_BROWSER_DL][download_by_media_url] "
                            f"ffmpeg_failed media_class={media_class} switching_to_http"
                        )

                        if media_class == "yandex_media_host":
                            temp_input_path = f"{filepath}.source"
                            try:
                                logger.info(
                                    "[YM_BROWSER_DL][download_by_media_url] "
                                    "strategy=http_to_temp_then_ffmpeg_transcode"
                                )
                                SimpleHTTPDownloadService.download(
                                    media_url, temp_input_path, headers=headers
                                )
                                FFmpegService.transcode_to_mp3(
                                    temp_input_path, filepath
                                )
                            finally:
                                try:
                                    if os.path.exists(temp_input_path):
                                        os.remove(temp_input_path)
                                except Exception:
                                    pass
                        else:
                            logger.info(
                                "[YM_BROWSER_DL][download_by_media_url] strategy=http_direct"
                            )
                            SimpleHTTPDownloadService.download(media_url, filepath)
            except (DownloadError, SimpleHTTPDownloadError) as exc:
                logger.warning(
                    f"[YM_BROWSER_DL] download_by_media_url_failed error={exc}"
                )

                if (
                    not retried_after_captcha
                ) and YandexSimpleDownloadService._is_captcha_error(exc):
                    logger.warning(
                        "[YM_BROWSER_DL][captcha] detected; requesting manual solve in browser"
                    )
                    solved = (
                        YandexSimpleDownloadService._open_and_wait_captcha_resolution(
                            browser_driver,
                            media_url,
                        )
                    )
                    if solved:
                        logger.info(
                            "[YM_BROWSER_DL][captcha] solved; retrying track download once"
                        )
                        return (
                            YandexSimpleDownloadService._download_via_browser_playback(
                                track_url,
                                filepath,
                                browser_driver,
                                retried_after_captcha=True,
                            )
                        )

                return False

            ok = YandexSimpleDownloadService._is_valid_audio_file(filepath)
            if not ok and os.path.exists(filepath):
                try:
                    os.remove(filepath)
                except Exception:
                    pass
            logger.info(
                f"[YM_BROWSER_DL] end success={ok} size={os.path.getsize(filepath) if os.path.exists(filepath) else 0}"
            )
            return ok
        except Exception as exc:
            logger.warning(f"[YM_BROWSER_DL] failed error={exc}")
            return False

    @staticmethod
    def _base_opts(filepath: str) -> dict:
        outtmpl = os.path.splitext(filepath)[0] + ".%(ext)s"
        return {
            "outtmpl": outtmpl,
            "format": "bestaudio/best",
            "noplaylist": True,
            "quiet": True,
            "no_warnings": True,
            "retries": 3,
            "fragment_retries": 3,
            "http_headers": {
                "User-Agent": (
                    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                    "AppleWebKit/537.36 (KHTML, like Gecko) "
                    "Chrome/123.0.0.0 Safari/537.36"
                ),
                "Referer": "https://music.yandex.ru/",
            },
            "postprocessors": [
                {
                    "key": "FFmpegExtractAudio",
                    "preferredcodec": "mp3",
                    "preferredquality": "320",
                }
            ],
        }

    @staticmethod
    def _build_attempts(
        base_opts: dict, selenium_cookie_file: str | None = None
    ) -> list[tuple[str, dict]]:
        attempts: list[tuple[str, dict]] = []

        if selenium_cookie_file:
            opt_selenium_cookies = deepcopy(base_opts)
            opt_selenium_cookies["cookiefile"] = selenium_cookie_file
            attempts.append(("cookies:selenium-session", opt_selenium_cookies))

        attempts.append(("plain", deepcopy(base_opts)))

        opt_default_chrome = deepcopy(base_opts)
        opt_default_chrome["cookiesfrombrowser"] = ("chrome",)
        attempts.append(("cookies:chrome", opt_default_chrome))

        opt_default_profile = deepcopy(base_opts)
        opt_default_profile["cookiesfrombrowser"] = ("chrome", None, None, "Default")
        attempts.append(("cookies:chrome-default-profile", opt_default_profile))

        opt_app_profile = deepcopy(base_opts)
        opt_app_profile["cookiesfrombrowser"] = ("chrome", PROFILE_DIR, None, "Default")
        attempts.append(("cookies:app-profile", opt_app_profile))

        return attempts

    @staticmethod
    def _export_selenium_cookies_to_file(browser_driver: Any) -> str | None:
        if not browser_driver:
            return None

        try:
            raw_cookies = browser_driver.get_cookies() or []
        except Exception as exc:
            logger.warning(f"[YM_DL_COOKIES] failed_to_read_from_driver error={exc}")
            return None

        ym_cookies = []
        for cookie in raw_cookies:
            domain = str(cookie.get("domain") or "").lower()
            if "yandex" in domain:
                ym_cookies.append(cookie)

        if not ym_cookies:
            logger.info("[YM_DL_COOKIES] no_yandex_cookies_in_driver")
            return None

        tmp_file = tempfile.NamedTemporaryFile(
            mode="w",
            encoding="utf-8",
            suffix=".cookies.txt",
            delete=False,
        )

        try:
            tmp_file.write("# Netscape HTTP Cookie File\n")
            for cookie in ym_cookies:
                domain = str(cookie.get("domain") or "").strip()
                if not domain:
                    continue

                include_subdomains = "TRUE"
                if not domain.startswith("."):
                    domain = f".{domain}"

                path = str(cookie.get("path") or "/")
                secure = "TRUE" if bool(cookie.get("secure")) else "FALSE"
                expiry = int(cookie.get("expiry") or 0)
                name = str(cookie.get("name") or "")
                value = str(cookie.get("value") or "")

                if not name:
                    continue

                if bool(cookie.get("httpOnly")):
                    domain = f"#HttpOnly_{domain}"

                tmp_file.write(
                    f"{domain}\t{include_subdomains}\t{path}\t{secure}\t{expiry}\t{name}\t{value}\n"
                )

            tmp_file.flush()
            logger.info(
                f"[YM_DL_COOKIES] exported_from_driver file={tmp_file.name} count={len(ym_cookies)}"
            )
            return tmp_file.name
        except Exception as exc:
            logger.warning(f"[YM_DL_COOKIES] failed_to_write_cookiefile error={exc}")
            return None
        finally:
            tmp_file.close()

    @staticmethod
    def download_track(
        track_url: str, filepath: str, browser_driver: Any = None
    ) -> bool:
        if not track_url or "music.yandex" not in track_url:
            logger.warning(
                f"[YM_DL_FAIL] reason=invalid_track_url track_url={track_url}"
            )
            return False

        logger.info(
            f"[YM_DL_START] track_url={track_url} filepath={filepath} profile_dir={PROFILE_DIR}"
        )
        os.makedirs(os.path.dirname(filepath), exist_ok=True)
        if os.path.exists(filepath):
            try:
                os.remove(filepath)
                logger.debug(f"[YM_DL_PREP] removed_existing_file={filepath}")
            except Exception as exc:
                logger.warning(
                    f"[YM_DL_PREP] failed_to_remove_existing_file error={exc}"
                )

        logger.info("[YM_DL_MODE] yandex_download_mode=browser_only")

        browser_fallback_ok = (
            YandexSimpleDownloadService._download_via_browser_playback(
                track_url,
                filepath,
                browser_driver,
            )
        )
        if browser_fallback_ok:
            logger.info("[YM_DL_OK] attempt=browser_playback_capture")
            return True

        logger.error(
            "[YM_DL_FAIL] reason=browser_capture_failed hint='re-login to Yandex and retry'"
        )

        return False
