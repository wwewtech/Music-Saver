import time
from selenium.webdriver.common.by import By
from src.config import (
    JS_PARSE_TRACKS,
    JS_EXPAND_BUTTON,
    JS_CLICK,
    JS_SCROLL_TO_BOTTOM,
    JS_SCROLL_HEIGHT,
)
from src.utils.logger import logger


class ParserService:
    def __init__(self, driver, user_id):
        self.driver = driver
        self.user_id = user_id

    def scan_playlists(self):
        logger.debug("ParserService.scan_playlists: start")
        if not self.user_id:
            logger.warning("scan_playlists called without user_id")
            return []

        url = f"https://vk.com/audios{self.user_id}?block=my_playlists&section=all"
        logger.debug(f"Navigating to {url}")
        self.driver.get(url)
        time.sleep(3)
        
        logger.info("Scrolling playlists...")
        self._scroll_to_end()

        playlists = []
        elements = self.driver.find_elements(By.CSS_SELECTOR, "div.audio_pl_item2")

        for el in elements:
            try:
                try:
                    title = el.find_element(By.CSS_SELECTOR, ".audio_pl__title").text
                except:
                    title = "Без названия"

                href = el.find_element(
                    By.CSS_SELECTOR, ".audio_pl__cover"
                ).get_attribute("href")

                if "playlist/" in href:
                    pid = href.split("playlist/")[1]
                else:
                    pid = href.split("/")[-1]

                playlists.append({"id": pid, "title": title, "url": href})
            except:
                pass
        return playlists

    def parse_tracks_from_page(self, url):
        self.driver.get(url)
        time.sleep(4)
        self._expand_playlist_fully()

        logger.info("Collecting metadata via JS...")
        tracks = self.driver.execute_script(JS_PARSE_TRACKS)
        if not tracks:
            logger.warning("Main parser returned 0 tracks.")
            return []

        return tracks

    def _scroll_to_end(self):
        last_h = 0
        while True:
            self.driver.execute_script(JS_SCROLL_TO_BOTTOM)
            time.sleep(1.5)
            curr_h = self.driver.execute_script(JS_SCROLL_HEIGHT)
            if curr_h == last_h:
                break
            last_h = curr_h

    def _expand_playlist_fully(self):
        logger.info("Expanding playlist tracks...")
        last_h = 0
        attempts = 0
        while True:
            try:
                expand_btns = self.driver.find_elements(
                    By.CSS_SELECTOR, "div[data-testid='audiolistitems-expandbutton']"
                )
                if expand_btns:
                    btn = expand_btns[0]
                    self.driver.execute_script(JS_EXPAND_BUTTON, btn)
                    time.sleep(0.5)
                    self.driver.execute_script(JS_CLICK, btn)
                    time.sleep(2)
                    continue
            except:
                pass

            self.driver.execute_script(JS_SCROLL_TO_BOTTOM)
            time.sleep(1.5)

            curr_h = self.driver.execute_script(JS_SCROLL_HEIGHT)
            if curr_h == last_h:
                attempts += 1
                if attempts >= 2:
                    break
            else:
                attempts = 0
            last_h = curr_h
