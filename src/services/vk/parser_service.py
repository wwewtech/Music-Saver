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
        logger.info(f"Переход на страницу плейлистов: {url}")
        self.driver.get(url)
        time.sleep(3)
        
        logger.info("Начинаем прокрутку списка плейлистов...")
        self._scroll_to_end()

        playlists = []
        logger.debug("Поиск элементов плейлистов на странице (div.audio_pl_item2)...")
        elements = self.driver.find_elements(By.CSS_SELECTOR, "div.audio_pl_item2")
        logger.info(f"Найдено DOM-элементов плейлистов: {len(elements)}")

        for i, el in enumerate(elements):
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
                logger.debug(f"Плейлист [{i}]: {title} (ID: {pid})")
            except Exception as e:
                logger.warning(f"Ошибка при парсинге элемента плейлиста [{i}]: {e}")
                pass
        
        logger.info(f"Успешно обработано плейлистов: {len(playlists)}")
        return playlists

    def parse_tracks_from_page(self, url):
        logger.info(f"Загрузка страницы плейлиста для парсинга треков: {url}")
        self.driver.get(url)
        time.sleep(4)
        
        logger.info("Раскрываем плейлист полностью (expand)...")
        self._expand_playlist_fully()

        logger.info("Вызов JS-скрипта для сбора метаданных треков...")
        tracks = self.driver.execute_script(JS_PARSE_TRACKS)
        if not tracks:
            logger.warning("Main parser JS вернул пустой список или 0 треков.")
            return []

        logger.info(f"JS-скрипт вернул {len(tracks)} треков.")
        return tracks

    def _scroll_to_end(self):
        last_h = 0
        scroll_attempts = 0
        while True:
            self.driver.execute_script(JS_SCROLL_TO_BOTTOM)
            time.sleep(1.5)
            curr_h = self.driver.execute_script(JS_SCROLL_HEIGHT)
            scroll_attempts += 1
            logger.debug(f"Scroll attempt {scroll_attempts}: height {curr_h}")
            if curr_h == last_h:
                logger.debug("Достигнут конец страницы (высота не изменилась).")
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
