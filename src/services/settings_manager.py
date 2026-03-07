import json
import os
from src.config import DATA_DIR
from src.utils.logger import logger

class SettingsManager:
    def __init__(self):
        self._settings_file = os.path.join(DATA_DIR, 'settings.json')
        self._settings = self._load_settings()

    def _load_settings(self):
        try:
            if not os.path.exists(self._settings_file):
                logger.info("Settings file not found. Creating default.")
                return {'tg_bot_token': '', 'tg_chat_id': ''}
            
            with open(self._settings_file, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception as e:
            logger.error(f"Error loading settings: {e}")
            return {'tg_bot_token': '', 'tg_chat_id': ''}

    def save_settings(self, token, chat_id):
        self._settings['tg_bot_token'] = token
        self._settings['tg_chat_id'] = chat_id
        
        try:
            with open(self._settings_file, 'w', encoding='utf-8') as f:
                json.dump(self._settings, f, indent=4)
        except Exception as e:
            logger.error(f"Error saving settings: {e}")

    def get_settings(self):
        return self._settings
