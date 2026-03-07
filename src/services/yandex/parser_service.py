import re
import time
import random
from typing import List, Dict, Tuple, Optional

import requests
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException

from src.utils.logger import logger


# ── JS: parse track elements from Yandex Music playlist DOM ──────────────
JS_YM_PARSE_TRACKS = """
const trackElements = document.querySelectorAll('[data-intersection-property-id^="tracks_track_"]');
const results = [];
trackElements.forEach(el => {
    const propId = el.getAttribute('data-intersection-property-id') || '';
    const trackId = propId.replace('tracks_track_', '');
    if (!trackId) return;

    let albumId = '';
    const albumLink = el.querySelector('a[href*="/album/"][href*="/track/"]');
    if (albumLink) {
        const m = albumLink.getAttribute('href').match(/\\/album\\/(\\d+)\\/track\\/(\\d+)/);
        if (m) albumId = m[1];
    }

    let title = '';
    const titleSpan = el.querySelector('[class*="Meta_title"]');
    if (titleSpan) title = titleSpan.textContent.trim();

    const artistSpans = el.querySelectorAll('[class*="Meta_artistCaption"]');
    const artists = Array.from(artistSpans).map(s => s.textContent.trim());

    let coverUrl = '';
    const img = el.querySelector('img[class*="PlayButtonWithCover_coverImage"]');
    if (img) {
        const srcset = img.getAttribute('srcset') || '';
        const parts = srcset.split(',');
        if (parts.length > 1) {
            coverUrl = parts[parts.length - 1].trim().split(' ')[0];
        } else {
            coverUrl = img.src || '';
        }
        coverUrl = coverUrl.replace(/\\/\\d+x\\d+$/, '/400x400');
    }

    let duration = 0;
    const durSpan = el.querySelector('[class*="CommonControlsBar_duration"] span[aria-hidden="true"]');
    if (durSpan) {
        const p = durSpan.textContent.trim().split(':');
        if (p.length >= 2) {
            duration = parseInt(p[0] || 0) * 60 + parseInt(p[1] || 0);
        }
    }

    results.push({
        track_id: trackId,
        album_id: albumId,
        title: title,
        artist: artists.join(', '),
        cover_url: coverUrl,
        duration: duration,
    });
});
return results;
"""

JS_YM_SCROLL_HEIGHT = "return document.body.scrollHeight;"
JS_YM_SCROLL_TO_BOTTOM = "window.scrollTo(0, document.body.scrollHeight);"

JS_YM_PLAYLIST_TITLE = """
const h = document.querySelector('[class*="PlaylistPage_title"], [class*="page-playlist__title"], h1');
return h ? h.textContent.trim() : '';
"""

JS_YM_COLLECTION_PLAYLISTS = """
const section = document.querySelector('section[data-intersection-property-id="COLLECTION_PLAYLISTS"]') || document;
const links = Array.from(section.querySelectorAll('a[href*="/playlists/"]'));
const seen = new Set();
const result = [];

for (const link of links) {
    const href = link.getAttribute('href') || '';
    const m = href.match(/\\/playlists\\/([^/?#]+)/);
    if (!m) continue;

    const slug = m[1];
    if (seen.has(slug)) continue;
    seen.add(slug);

    const rawTitle = (link.textContent || '').trim();
    const title = rawTitle || `playlist_${slug}`;

    const fullUrl = href.startsWith('http') ? href : `https://music.yandex.ru/playlists/${slug}`;
    result.push({
        id: `ym:collection:${slug}`,
        slug,
        title,
        url: fullUrl,
    });
}

return result;
"""


class YandexParserService:
    """Service for parsing Yandex Music playlists via Selenium and Chart API."""

    CHART_URL = "https://music.yandex.ru/handlers/main.jsx"
    CHART_PAGE_URL = "https://music.yandex.ru/chart"

    def __init__(self, driver=None, language: str = "ru"):
        self.driver = driver
        self.language = language if language in {"ru", "en"} else "ru"

    # ── Public helpers ──────────────────────────────────────────────────

    @staticmethod
    def make_playlist_id(url: str) -> str:
        """Generate a stable playlist id from Yandex Music URL."""
        slug = url.rstrip("/").split("/")[-1]
        return f"ym:{slug}"

    def get_chart_playlist(self) -> Dict:
        return {
            "id": "ym:chart:top100",
            "title": "Yandex Music — Chart Top 100",
            "url": self.CHART_PAGE_URL,
        }

    # ── Selenium-based playlist parsing ─────────────────────────────────

    def parse_playlist_page(self, url: str) -> Tuple[str, List[Dict]]:
        """Navigate to a Yandex Music playlist URL and extract all tracks.

        Returns ``(playlist_title, list_of_track_dicts)``.
        """
        if not self.driver:
            raise RuntimeError("Selenium driver is required for playlist parsing")

        logger.info(f"YandexParser: navigating to {url}")
        self.driver.get(url)
        time.sleep(4)

        # Playlist title
        title = self.driver.execute_script(JS_YM_PLAYLIST_TITLE) or "Yandex Music Playlist"

        # Scroll to lazy-load all tracks (handles playlists > 100 tracks)
        self._scroll_to_load_all()

        # Extract tracks from DOM
        raw_tracks = self.driver.execute_script(JS_YM_PARSE_TRACKS)
        if not raw_tracks:
            logger.warning("YandexParser: no tracks found on page")
            return title, []

        tracks = self._normalize_tracks(raw_tracks)
        logger.info(f"YandexParser: parsed {len(tracks)} tracks from '{title}'")
        return title, tracks

    def prepare_collection_for_manual_login(self, login_timeout_seconds: int = 180) -> bool:
        """Open Yandex Music, wait until user logs in, then open Collection page."""
        if not self.driver:
            raise RuntimeError("Selenium driver is required for Yandex login flow")

        logger.info("YandexParser: opening music.yandex.ru")
        self.driver.get("https://music.yandex.ru/")

        time.sleep(2)
        self._close_paywall_modal_if_present()

        if not self._wait_for_login(login_timeout_seconds):
            return False

        logger.info("YandexParser: login detected, opening /collection")
        self.driver.get("https://music.yandex.ru/collection")
        WebDriverWait(self.driver, 30).until(
            EC.presence_of_element_located((By.CSS_SELECTOR, "body"))
        )
        time.sleep(1)
        self._close_paywall_modal_if_present()
        return True

    def parse_collection_playlists(self) -> List[Dict]:
        """Parse user playlists from Yandex Music Collection page."""
        if not self.driver:
            raise RuntimeError("Selenium driver is required for collection parsing")

        self._open_collection_playlists_section()
        time.sleep(2)

        raw = self.driver.execute_script(JS_YM_COLLECTION_PLAYLISTS) or []
        if not raw:
            logger.warning("YandexParser: no playlists found in collection")
            return []

        logger.info(f"YandexParser: collection playlists parsed={len(raw)}")
        return raw

    # ── Chart API parsing (no Selenium required) ────────────────────────

    def parse_chart_tracks(self) -> List[Dict]:
        params = {
            "what": "chart",
            "lang": self.language,
            "external-domain": "music.yandex.ru",
            "overembed": "false",
            "ncrnd": str(random.random()),
        }
        headers = {
            "Accept": "application/json, text/javascript, */*; q=0.01",
            "Referer": self.CHART_PAGE_URL,
            "User-Agent": (
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                "AppleWebKit/537.36 (KHTML, like Gecko) "
                "Chrome/122.0.0.0 Safari/537.36"
            ),
            "X-Requested-With": "XMLHttpRequest",
        }

        logger.info("YandexParserService: requesting chart data")
        response = requests.get(self.CHART_URL, params=params, headers=headers, timeout=20)
        response.raise_for_status()
        data = response.json()

        chart_positions = data.get("chartPositions", [])
        tracks: List[Dict] = []
        for item in chart_positions:
            track = item.get("track", {})
            track_id = track.get("id")
            if not track_id:
                continue

            albums = track.get("albums") or []
            album_id = str(albums[0].get("id")) if albums else ""
            artists = track.get("artists") or []
            artist_names = ", ".join(a.get("name", "") for a in artists if a.get("name"))
            cover_uri = track.get("coverUri", "")
            cover_url = f"https://{cover_uri.replace('%%', '400x400')}" if cover_uri else ""

            tracks.append(
                {
                    "id": f"ym_{track_id}_{album_id or 0}",
                    "owner_id": "yandex",
                    "audio_id": str(track_id),
                    "album_id": album_id,
                    "artist": artist_names or "Unknown",
                    "title": track.get("title") or "Unknown",
                    "subtitle": track.get("version") or "",
                    "duration": int(track.get("durationMs", 0) / 1000),
                    "cover_url": cover_url,
                    "url": f"https://music.yandex.ru/album/{album_id}/track/{track_id}" if album_id else "",
                    "source": "yandex",
                }
            )

        logger.info(f"YandexParserService: chart tracks={len(tracks)}")
        return tracks

    # ── Internal helpers ────────────────────────────────────────────────

    def _scroll_to_load_all(self):
        """Scroll page to trigger lazy-loading of all tracks."""
        last_h = 0
        stable_rounds = 0
        for _ in range(60):  # safety cap
            self.driver.execute_script(JS_YM_SCROLL_TO_BOTTOM)
            time.sleep(1.5)
            curr_h = self.driver.execute_script(JS_YM_SCROLL_HEIGHT)
            if curr_h == last_h:
                stable_rounds += 1
                if stable_rounds >= 3:
                    break
            else:
                stable_rounds = 0
            last_h = curr_h

    def _wait_for_login(self, timeout_seconds: int) -> bool:
        """Wait until the left navigation appears (signal that user is logged in)."""
        try:
            WebDriverWait(self.driver, timeout_seconds).until(
                EC.presence_of_element_located((By.CSS_SELECTOR, "aside[class*='Navbar_root']"))
            )
            logger.info("YandexParser: login signal detected (Navbar)")
            return True
        except TimeoutException:
            logger.warning("YandexParser: login wait timeout")
            return False

    def _close_paywall_modal_if_present(self):
        """Attempt to close paywall modal if it appears."""
        try:
            close_buttons = self.driver.find_elements(
                By.CSS_SELECTOR,
                "header[class*='PaywallModal_header'] button[aria-label='Закрыть']",
            )
            for btn in close_buttons:
                if btn.is_displayed() and btn.is_enabled():
                    self.driver.execute_script("arguments[0].click();", btn)
                    logger.info("YandexParser: paywall modal closed")
                    time.sleep(0.5)
                    break
        except Exception as exc:
            logger.debug(f"YandexParser: paywall close skipped ({exc})")

    def _open_collection_playlists_section(self):
        """Open collection playlists by URL and ensure section is visible."""
        self.driver.get("https://music.yandex.ru/collection/playlists")
        try:
            WebDriverWait(self.driver, 30).until(
                EC.presence_of_element_located((By.CSS_SELECTOR, "section[data-intersection-property-id='COLLECTION_PLAYLISTS'], a[href*='/playlists/']"))
            )
            logger.info("YandexParser: opened /collection/playlists")
            return
        except TimeoutException:
            logger.warning("YandexParser: /collection/playlists did not load in time, trying fallback")

        self.driver.get("https://music.yandex.ru/collection")
        WebDriverWait(self.driver, 30).until(
            EC.presence_of_element_located((By.CSS_SELECTOR, "body"))
        )

        try:
            playlists_link = WebDriverWait(self.driver, 20).until(
                EC.element_to_be_clickable((By.CSS_SELECTOR, "a[href='/collection/playlists'], a[href*='/collection/playlists']"))
            )
            self.driver.execute_script("arguments[0].click();", playlists_link)
            WebDriverWait(self.driver, 30).until(
                EC.presence_of_element_located((By.CSS_SELECTOR, "section[data-intersection-property-id='COLLECTION_PLAYLISTS'], a[href*='/playlists/']"))
            )
            logger.info("YandexParser: playlists section opened via Collection page link")
        except TimeoutException:
            logger.warning("YandexParser: playlists section not found after fallback navigation")

    @staticmethod
    def _normalize_tracks(raw_tracks: List[Dict]) -> List[Dict]:
        """Convert raw JS-extracted dicts into the unified track dict format."""
        tracks: List[Dict] = []
        for t in raw_tracks:
            track_id = str(t.get("track_id", ""))
            album_id = str(t.get("album_id", ""))
            if not track_id:
                continue

            track_url = ""
            if album_id:
                track_url = f"https://music.yandex.ru/album/{album_id}/track/{track_id}"

            tracks.append(
                {
                    "id": f"ym_{track_id}_{album_id or 0}",
                    "owner_id": "yandex",
                    "audio_id": track_id,
                    "album_id": album_id,
                    "artist": t.get("artist") or "Unknown",
                    "title": t.get("title") or "Unknown",
                    "subtitle": "",
                    "duration": t.get("duration", 0),
                    "cover_url": t.get("cover_url", ""),
                    "url": track_url,
                    "source": "yandex",
                }
            )
        return tracks
