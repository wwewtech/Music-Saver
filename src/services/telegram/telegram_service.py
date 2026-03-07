import time
import os
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

    def create_topic(self, topic_name):
        """Creates a forum topic in the group and returns its ID."""
        if not self.bot or not self.chat_id:
            return None

        try:
            # Limit name length (Telegram limit is 128, example uses 120)
            safe_name = topic_name[:120]
            # Check if chat is a forum (supergroup with topics enabled)
            # But the simplest way is just try to create.
            # Note: create_forum_topic returns a ForumTopic object which has message_thread_id
            topic = self.bot.create_forum_topic(chat_id=self.chat_id, name=safe_name)
            logger.info(
                f"Created Telegram topic '{safe_name}' with ID: {topic.message_thread_id}"
            )
            time.sleep(2)  # Avoid aggressive rate limiting immediately after creation
            return topic.message_thread_id
        except ApiTelegramException as e:
            logger.error(f"Failed to create topic '{topic_name}': {e}")
            if "not enough rights" in str(e):
                logger.warning("Bot needs 'Manage Topics' permission to create albums.")
            elif "topics not enabled" in str(e):
                logger.warning("Target group does not have Topics enabled.")
            return None
        except Exception as e:
            logger.error(f"Unexpected error creating topic: {e}")
            return None

    def send_test_message(self, text):
        if not self.bot or not self.chat_id:
            return False, "Bot token or Chat ID not set."
        try:
            self.bot.send_message(self.chat_id, text)
            return True, "Message sent successfully!"
        except Exception as e:
            return False, str(e)

    def upload_track(
        self, file_path, caption, artist, title, duration, topic_id=None, thumbnail=None
    ):
        if not self.bot or not self.chat_id:
            logger.info("Telegram configuration missing. Skipping upload.")
            return None

        file_size = os.path.getsize(file_path)
        logger.info(
            f"Начало загрузки в ТГ: {title} ({file_size} байт) [TopicID: {topic_id}]"
        )

        if thumbnail:
            logger.debug(f"Получена обложка для трека. Размер: {len(thumbnail)} байт")
        else:
            logger.debug("Обложка не передана для этого трека.")

        attempts = 0
        while True:
            attempts += 1
            try:
                logger.debug(f"Попытка загрузки #{attempts} для {file_path}")
                with open(file_path, "rb") as audio:
                    # Note: We use 'thumb' parameter which is standard in pyTelegramBotAPI for send_audio
                    msg = self.bot.send_audio(
                        chat_id=self.chat_id,
                        message_thread_id=topic_id,
                        audio=audio,
                        caption=caption,
                        performer=artist,
                        title=title,
                        duration=duration,
                        thumb=thumbnail,
                    )
                    logger.info(
                        f"Успешно загружено в Telegram: {title} (MessageID: {msg.message_id})"
                    )
                    return msg
            except ApiTelegramException as e:
                # Handle rate limiting
                if e.error_code == 429:
                    retry_after = 5
                    if (
                        hasattr(e, "result_json")
                        and "parameters" in e.result_json
                        and "retry_after" in e.result_json["parameters"]
                    ):
                        retry_after = int(e.result_json["parameters"]["retry_after"])

                    logger.warning(
                        f"Telegram FloodWait (429): Ожидание {retry_after} секунд... (Попытка {attempts})"
                    )
                    time.sleep(retry_after)
                    continue
                else:
                    logger.error(
                        f"Telegram API Error ({e.error_code}): {e.description}"
                    )
                    raise e
            except Exception as e:
                logger.error(
                    f"Непредвиденная ошибка при загрузке в Telegram: {type(e).__name__}: {e}"
                )
                raise e
