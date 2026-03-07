from src.config import JS_UNKASK_URL
from src.utils.logger import logger


class LinkDecoder:
    def __init__(self, driver):
        self.driver = driver

    def get_audio_url(self, track_dict):
        """
        Expects a dictionary representation of the track (as returned by parser).
        """
        logger.debug(f"Попытка декодирования ссылки для трека {track_dict.get('id')}...")
        try:
            result = self.driver.execute_script(JS_UNKASK_URL, track_dict)
            if result and result[1] and result[1].startswith("http"):
                logger.debug(f"Успешно декодирована ссылка для {track_dict.get('id')}: {result[1][:50]}...")
                return result[1]
            else:
                logger.warning(f"Декодирование ссылки для {track_dict.get('id')} не дало результата: {result}")
                return None
        except Exception as e:
            logger.error(f"Ошибка LinkDecoder для трека {track_dict.get('id')}: {e}")
            return None
