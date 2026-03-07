from src.config import JS_UNKASK_URL
from src.utils.logger import logger


class LinkDecoder:
    def __init__(self, driver):
        self.driver = driver

    def get_audio_url(self, track_dict):
        """
        Expects a dictionary representation of the track (as returned by parser).
        """
        try:
            result = self.driver.execute_script(JS_UNKASK_URL, track_dict)
            if result and result[1] and result[1].startswith("http"):
                return result[1]
            else:
                logger.debug(f"Link decode failed: {result}")
                return None
        except Exception as e:
            logger.error(f"LinkDecoder error: {e}")
            return None
