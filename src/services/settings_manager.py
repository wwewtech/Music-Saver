import json
import os
import tempfile

try:
    import tomllib
except ModuleNotFoundError:  # pragma: no cover - Python 3.10 fallback
    import tomli as tomllib

from src.app_config import DEFAULT_SETTINGS, LEGACY_SETTINGS_PATH, SETTINGS_PATH
from src.utils.logger import logger


class SettingsManager:
    def __init__(self):
        self._settings_file = SETTINGS_PATH
        self._settings = self._load_settings()

    @staticmethod
    def _default_settings():
        return dict(DEFAULT_SETTINGS)

    def _normalize_settings(self, values):
        defaults = self._default_settings()
        normalized = dict(defaults)
        normalized.update(values or {})

        normalized["tg_bot_token"] = str(normalized.get("tg_bot_token", "") or "")
        normalized["tg_chat_id"] = str(normalized.get("tg_chat_id", "") or "")

        if normalized.get("processing_strategy") not in {
            "download_only",
            "download_upload",
            "direct_transfer",
        }:
            normalized["processing_strategy"] = defaults["processing_strategy"]

        if normalized.get("preferred_source") not in {"vk", "yandex"}:
            normalized["preferred_source"] = defaults["preferred_source"]

        if normalized.get("language") not in {"ru", "en"}:
            normalized["language"] = defaults["language"]

        normalized["setup_completed"] = bool(normalized.get("setup_completed", False))

        download_path = normalized.get("download_path", "")
        normalized["download_path"] = download_path if isinstance(download_path, str) else ""
        return normalized

    def _load_legacy_settings(self):
        if not os.path.exists(LEGACY_SETTINGS_PATH):
            return None

        try:
            import json

            with open(LEGACY_SETTINGS_PATH, "r", encoding="utf-8") as file_obj:
                loaded = json.load(file_obj)
            if isinstance(loaded, dict):
                logger.info("Migrating legacy settings.json to settings.toml")
                return loaded
        except Exception as exc:
            logger.warning(f"Failed to read legacy settings.json: {exc}")
        return None

    def _load_settings(self):
        defaults = self._default_settings()
        try:
            if not os.path.exists(self._settings_file):
                legacy = self._load_legacy_settings()
                normalized = self._normalize_settings(legacy or defaults)
                self._settings = normalized
                self._save_to_file()
                return normalized

            with open(self._settings_file, "rb") as file_obj:
                loaded = tomllib.load(file_obj)
            return self._normalize_settings(loaded)
        except Exception as exc:
            logger.error(f"Error loading settings: {exc}")
            normalized = self._normalize_settings(defaults)
            self._settings = normalized
            return normalized

    @staticmethod
    def _serialize_toml_value(value):
        if isinstance(value, bool):
            return "true" if value else "false"
        if isinstance(value, (int, float)) and not isinstance(value, bool):
            return str(value)
        return json.dumps(str(value), ensure_ascii=False)

    def _dump_settings(self, file_obj):
        lines = [
            f"{key} = {self._serialize_toml_value(value)}"
            for key, value in self._settings.items()
        ]
        payload = "\n".join(lines) + "\n"
        file_obj.write(payload.encode("utf-8"))

    def save_settings(self, token, chat_id):
        self._settings["tg_bot_token"] = token
        self._settings["tg_chat_id"] = chat_id
        self._save_to_file()

    def get_settings(self):
        return dict(self._settings)

    def get(self, key, default=None):
        return self._settings.get(key, default)

    def set(self, key, value):
        self._settings[key] = value
        self._save_to_file()

    def _save_to_file(self):
        temp_path = None
        try:
            os.makedirs(os.path.dirname(self._settings_file), exist_ok=True)
            with tempfile.NamedTemporaryFile(
                mode="wb",
                delete=False,
                dir=os.path.dirname(self._settings_file),
                suffix=".tmp",
            ) as file_obj:
                temp_path = file_obj.name
                self._dump_settings(file_obj)
            os.replace(temp_path, self._settings_file)
        except Exception as exc:
            logger.error(f"Error saving settings: {exc}")
            if temp_path and os.path.exists(temp_path):
                try:
                    os.remove(temp_path)
                except OSError:
                    pass
