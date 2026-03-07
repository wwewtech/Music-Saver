import os
import re
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.common.exceptions import SessionNotCreatedException
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

from src.config import CHROMEDRIVER_PATH, PROFILE_DIR
from src.utils.logger import logger


class VKDriverFactory:
    @staticmethod
    def create_driver():
        logger.info(f"Создание Selenium Driver. Путь к профилю: {PROFILE_DIR}")
        selenium_cache_dir = os.path.join(
            os.path.dirname(PROFILE_DIR), "selenium_cache"
        )
        os.makedirs(selenium_cache_dir, exist_ok=True)
        os.environ.setdefault("SE_CACHE_PATH", selenium_cache_dir)
        options = Options()
        options.add_argument(f"user-data-dir={PROFILE_DIR}")
        options.add_argument("--disable-blink-features=AutomationControlled")
        options.add_experimental_option("excludeSwitches", ["enable-automation"])
        options.set_capability("goog:loggingPrefs", {"performance": "ALL"})
        options.add_argument("--mute-audio")
        options.add_argument("--log-level=3")
        options.add_argument("--disable-application-cache")
        options.add_argument("--disk-cache-size=0")
        options.add_argument("--disable-gpu")
        options.add_argument("--no-sandbox")

        logger.debug(f"Используемый ChromeDriver: {CHROMEDRIVER_PATH}")
        driver = None

        try:
            if os.path.exists(CHROMEDRIVER_PATH):
                service = Service(CHROMEDRIVER_PATH)
                driver = webdriver.Chrome(service=service, options=options)
                logger.info(
                    "Selenium Chrome Driver успешно запущен (локальный chromedriver.exe)."
                )
            else:
                logger.warning(
                    "Локальный chromedriver.exe не найден. Переход на Selenium Manager."
                )
                driver = webdriver.Chrome(options=options)
                logger.info(
                    "Selenium Chrome Driver успешно запущен через Selenium Manager."
                )
        except SessionNotCreatedException as e:
            logger.warning(
                "Локальный ChromeDriver не подходит к версии Chrome. "
                "Пробуем Selenium Manager для автоподбора драйвера..."
            )
            try:
                driver = webdriver.Chrome(options=options)
                logger.info(
                    "Selenium Chrome Driver успешно запущен через Selenium Manager после fallback."
                )
            except Exception as fallback_error:
                logger.error(
                    f"Ошибка при создании Chrome Driver через Selenium Manager: {fallback_error}"
                )
                raise fallback_error
        except Exception as e:
            logger.error(f"Ошибка при создании Chrome Driver: {e}")
            raise e

        try:
            logger.debug("Отключение кэша браузера через CDP...")
            driver.execute_cdp_cmd("Network.enable", {})
            driver.execute_cdp_cmd("Network.setCacheDisabled", {"cacheDisabled": True})
        except Exception as e:
            logger.warning(f"Не удалось отключить кэш через CDP: {e}")

        return driver
