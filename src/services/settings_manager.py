import json
import os
from src.config import DATA_DIR
from src.utils.logger import logger

class SettingsManager:
    def __init__(self):
        self._settings_file = os.path.join(DATA_DIR, 'settings.json')
        self._settings = self._load_settings()

    @staticmethod
    def _default_settings():
        return {
            'tg_bot_token': '',
            'tg_chat_id': '',
            'processing_strategy': 'download_only',
            'language': 'ru',
            'setup_completed': False,
            'download_path': 'data/downloads',
        }

    def _load_settings(self):
        try:
            if not os.path.exists(self._settings_file):
                logger.info("Settings file not found. Creating default.")
                return self._default_settings()
            
            with open(self._settings_file, 'r', encoding='utf-8') as f:
                loaded = json.load(f)
                defaults = self._default_settings()
                defaults.update(loaded)
                return defaults
        except Exception as e:
            logger.error(f"Error loading settings: {e}")
            return self._default_settings()

    def save_settings(self, token, chat_id):
        self._settings['tg_bot_token'] = token
        self._settings['tg_chat_id'] = chat_id
        self._save_to_file()

    def get_settings(self):
        return self._settings

    def get(self, key, default=None):
        return self._settings.get(key, default)

    def set(self, key, value):
        self._settings[key] = value
        self._save_to_file()

    def _save_to_file(self):
        try:
            with open(self._settings_file, 'w', encoding='utf-8') as f:
                json.dump(self._settings, f, indent=4)
        except Exception as e:
            logger.error(f"Error saving settings: {e}")
