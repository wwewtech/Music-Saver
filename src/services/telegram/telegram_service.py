import time
import telebot
from telebot.apihelper import ApiTelegramException
from src.utils.logger import logger

class TelegramService:
    def __init__(self, bot_token, chat_id):
        self.chat_id = chat_id
        if bot_token:
            self.bot = telebot.TeleBot(bot_token)
        else:
            self.bot = None

    def verify_permissions(self):
        if not self.bot or not self.chat_id:
            return False
        try:
            # Try to get chat info
            self.bot.get_chat(self.chat_id)
            return True
        except ApiTelegramException as e:
            logger.error(f"Telegram permission check failed: {e}")
            return False
        except Exception as e:
            logger.error(f"Unexpected error in verify_permissions: {e}")
            return False

    def upload_track(self, file_path, caption, artist, title, duration):
        if not self.bot or not self.chat_id:
            logger.info("Telegram configuration missing. Skipping upload.")
            return None

        while True:
            try:
                with open(file_path, 'rb') as audio:
                    msg = self.bot.send_audio(
                        chat_id=self.chat_id,
                        audio=audio,
                        caption=caption,
                        performer=artist,
                        title=title,
                        duration=duration
                    )
                    logger.info(f"Successfully uploaded track to Telegram: {title}")
                    return msg
            except ApiTelegramException as e:
                # Handle rate limiting
                if e.error_code == 429:
                    retry_after = 5
                    if hasattr(e, 'result_json') and 'parameters' in e.result_json and 'retry_after' in e.result_json['parameters']:
                        retry_after = int(e.result_json['parameters']['retry_after'])
                    
                    logger.warning(f"Telegram rate limited (FloodWait). Sleeping for {retry_after}s...")
                    time.sleep(retry_after)
                    continue
                else:
                    logger.error(f"Failed to upload to Telegram: {e}")
                    raise e
            except Exception as e:
                logger.error(f"Unexpected error uploading to Telegram: {e}")
                raise e
