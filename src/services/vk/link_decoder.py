from src.app_config import JS_UNKASK_URL
from src.utils.logger import logger


class LinkDecoder:
    def __init__(self, driver):
        self.driver = driver

    def get_audio_url(self, track_dict):
        """
        Expects a dictionary representation of the track (as returned by parser).
        """
        track_id = track_dict.get("id")
        logger.debug(
            "[VK_LINK_DECODE_START] "
            f"track_id={track_id} has_url={bool(track_dict.get('url'))} "
            f"has_access_key={bool(track_dict.get('access_key'))} has_action_hash={bool(track_dict.get('action_hash'))} "
            f"has_url_hash={bool(track_dict.get('url_hash'))}"
        )

        if not self.driver:
            logger.warning(
                f"[VK_LINK_DECODE_FAIL] reason=no_driver track_id={track_id}"
            )
            return None

        try:
            result = self.driver.execute_script(JS_UNKASK_URL, track_dict)
            plan = (
                result[0]
                if isinstance(result, (list, tuple)) and len(result) > 0
                else None
            )
            payload = (
                result[1]
                if isinstance(result, (list, tuple)) and len(result) > 1
                else None
            )

            if payload and isinstance(payload, str) and payload.startswith("http"):
                logger.info(
                    f"[VK_LINK_DECODE_OK] track_id={track_id} plan={plan} url_prefix={payload[:60]}"
                )
                return payload

            logger.warning(
                f"[VK_LINK_DECODE_FAIL] reason=no_http_url track_id={track_id} plan={plan} payload={payload} raw={result}"
            )
            return None
        except Exception as e:
            logger.exception(
                f"[VK_LINK_DECODE_FAIL] reason=exception track_id={track_id} error={e}"
            )
            return None
