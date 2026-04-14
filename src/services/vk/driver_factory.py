import os
import re
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.common.exceptions import SessionNotCreatedException
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

from src.app_config import PROFILE_DIR
from src.utils.logger import logger


class VKDriverFactory:
    @staticmethod
    def create_driver():
        logger.info(f"Создание Selenium Driver. Путь к профилю: {PROFILE_DIR}")
        logger.warning(
            "SECURITY: Chrome profile хранит cookie-файлы сессий VK/Yandex. "
            f"Путь: {PROFILE_DIR}. Ограничьте доступ к этой директории."
        )

        # Настройка кастомного пути для кэша Selenium, чтобы избежать проблем с правами доступа в .cache
        selenium_cache_dir = os.path.join(
            os.path.dirname(PROFILE_DIR), "selenium_cache"
        )
        os.makedirs(selenium_cache_dir, exist_ok=True)
        os.environ["SE_CACHE_PATH"] = selenium_cache_dir

        options = Options()
        options.add_argument(f"user-data-dir={PROFILE_DIR}")
        options.add_argument("--disable-blink-features=AutomationControlled")
        options.add_experimental_option("excludeSwitches", ["enable-automation"])
        options.set_capability("goog:loggingPrefs", {"performance": "ALL"})
        options.add_argument("--mute-audio")
        options.add_argument("--log-level=3")
        options.add_argument("--disable-gpu")
        options.add_argument("--no-sandbox")
        # Reduce memory usage: limit renderer processes and disable unneeded features
        options.add_argument("--disable-extensions")
        options.add_argument("--disable-dev-shm-usage")
        options.add_argument("--renderer-process-limit=2")

        try:
            # Используем встроенный Selenium Manager (Selenium 4.10+)
            # Он автоматически скачает драйвер, если его нет
            driver = webdriver.Chrome(options=options)
            logger.info("Chrome Driver успешно запущен через Selenium Manager.")
        except Exception as e:
            logger.error(f"Ошибка при создании Chrome Driver: {e}")
            raise e

        try:
            driver.execute_cdp_cmd(
                "Network.enable",
                {
                    "maxTotalBufferSize": 10
                    * 1024
                    * 1024,  # 10 MB max instead of unlimited
                    "maxResourceBufferSize": 5 * 1024 * 1024,  # 5 MB per resource
                },
            )
            driver.execute_cdp_cmd("Network.setCacheDisabled", {"cacheDisabled": True})
        except Exception as e:
            logger.warning(f"Не удалось настроить Network через CDP: {e}")

        return driver

    @staticmethod
    def flush_performance_logs(driver):
        """Drain Chrome performance logs to free memory. Call periodically."""
        try:
            driver.get_log("performance")
        except Exception:
            pass
