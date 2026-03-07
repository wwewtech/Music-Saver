import re
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.by import By
from src.utils.logger import logger


class AuthService:
    def __init__(self, driver):
        self.driver = driver
        self.user_id = None

    def wait_for_login(self, timeout=600):
        logger.debug(
            f"AuthService: переходим на vk.com и ждем логина (timeout={timeout}s)"
        )
        self.driver.get("https://vk.com")
        try:
            WebDriverWait(self.driver, timeout).until(
                EC.presence_of_element_located((By.ID, "l_aud"))
            )
            # Try getting ID from href
            try:
                link = self.driver.find_element(
                    By.CSS_SELECTOR, "#l_aud a"
                ).get_attribute("href")
                logger.debug(f"Найдена ссылка на аудио: {link}")
                match = re.search(r"audios(-?\d+)", link)
                if match:
                    self.user_id = match.group(1)
                    logger.debug(f"ID пользователя извлечен из ссылки: {self.user_id}")
                    return self.user_id
            except Exception:
                pass

            # Try JS
            uid = self.driver.execute_script("return window.vk ? window.vk.id : null;")
            if uid:
                self.user_id = str(uid)
                return self.user_id

        except Exception:
            return None
        return None
