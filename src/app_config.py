from __future__ import annotations

import sys
from pathlib import Path
from typing import Any

try:
    import tomllib
except ModuleNotFoundError:  # pragma: no cover - Python 3.10 fallback
    import tomli as tomllib


_BASE_DIR_PATH = Path(__file__).resolve().parent.parent

if getattr(sys, "frozen", False):
    _APP_DIR_PATH = Path(sys.executable).resolve().parent
    if hasattr(sys, "_MEIPASS"):
        _RESOURCE_DIR_PATH = Path(sys._MEIPASS)
    else:
        internal_dir = _APP_DIR_PATH / "_internal"
        _RESOURCE_DIR_PATH = internal_dir if internal_dir.exists() else _APP_DIR_PATH
else:
    _APP_DIR_PATH = _BASE_DIR_PATH
    _RESOURCE_DIR_PATH = _BASE_DIR_PATH


def _read_toml(path: Path) -> dict[str, Any]:
    with path.open("rb") as file_obj:
        return tomllib.load(file_obj)


def _resolve_defaults_path() -> Path:
    candidates = [
        _RESOURCE_DIR_PATH / "resources" / "app.default.toml",
        _APP_DIR_PATH / "resources" / "app.default.toml",
        _BASE_DIR_PATH / "resources" / "app.default.toml",
    ]
    for candidate in candidates:
        if candidate.is_file():
            return candidate
    raise FileNotFoundError(
        "app.default.toml not found. Expected one of: "
        + ", ".join(str(path) for path in candidates)
    )


DEFAULT_CONFIG_PATH = _resolve_defaults_path()
_APP_CONFIG = _read_toml(DEFAULT_CONFIG_PATH)

APP_METADATA = dict(_APP_CONFIG.get("app", {}))
UI_DEFAULTS = dict(_APP_CONFIG.get("ui", {}))
_STORAGE = dict(_APP_CONFIG.get("storage", {}))
DEFAULT_SETTINGS = dict(_APP_CONFIG.get("settings", {}).get("defaults", {}))

APP_NAME = str(APP_METADATA.get("name", "VK Music Saver"))
APP_VERSION = str(APP_METADATA.get("version", "1.0.0"))
APP_ID = str(APP_METADATA.get("app_id", "com.vkmusicsaver.app"))
UI_APPEARANCE_MODE = str(UI_DEFAULTS.get("appearance_mode", "Dark"))
UI_COLOR_THEME = str(UI_DEFAULTS.get("color_theme", "blue"))

BASE_DIR = str(_BASE_DIR_PATH)
APP_DIR = str(_APP_DIR_PATH)
RESOURCE_DIR = str(_RESOURCE_DIR_PATH)

DATA_DIR_PATH = _APP_DIR_PATH / str(_STORAGE.get("data_dir", "data"))
BIN_DIR_PATH = _APP_DIR_PATH / str(_STORAGE.get("bin_dir", "bin"))
PROFILE_DIR_PATH = DATA_DIR_PATH / str(_STORAGE.get("profile_dir", "chrome_profile"))
DOWNLOAD_DIR_PATH = DATA_DIR_PATH / str(_STORAGE.get("download_dir", "downloads"))
DB_PATH_PATH = DATA_DIR_PATH / str(_STORAGE.get("database_file", "vk_music.db"))
LOG_PATH_PATH = DATA_DIR_PATH / str(_STORAGE.get("log_file", "app.log"))
SETTINGS_PATH_PATH = DATA_DIR_PATH / str(_STORAGE.get("settings_file", "settings.toml"))
LEGACY_SETTINGS_PATH_PATH = DATA_DIR_PATH / "settings.json"

for required_dir in (DATA_DIR_PATH, PROFILE_DIR_PATH, DOWNLOAD_DIR_PATH, BIN_DIR_PATH):
    required_dir.mkdir(parents=True, exist_ok=True)

BIN_DIR = str(BIN_DIR_PATH)
DATA_DIR = str(DATA_DIR_PATH)
PROFILE_DIR = str(PROFILE_DIR_PATH)
DOWNLOAD_DIR = str(DOWNLOAD_DIR_PATH)
DB_PATH = str(DB_PATH_PATH)
LOG_PATH = str(LOG_PATH_PATH)
SETTINGS_PATH = str(SETTINGS_PATH_PATH)
LEGACY_SETTINGS_PATH = str(LEGACY_SETTINGS_PATH_PATH)

FFMPEG_PATH = ""
for candidate in (
    BIN_DIR_PATH / ("ffmpeg.exe" if sys.platform == "win32" else "ffmpeg"),
    _RESOURCE_DIR_PATH / "bin" / ("ffmpeg.exe" if sys.platform == "win32" else "ffmpeg"),
):
    if candidate.is_file():
        FFMPEG_PATH = str(candidate)
        break

VK_GENRES = {
    int(key): value
    for key, value in _APP_CONFIG.get("vk", {}).get("genres", {}).items()
}

_JS = _APP_CONFIG.get("js", {})
JS_FIND_USER_ID = str(_JS.get("find_user_id", "return window.vk ? window.vk.id : null;"))
JS_SCROLL_HEIGHT = str(_JS.get("scroll_height", "return document.body.scrollHeight"))
JS_SCROLL_TO_BOTTOM = str(
    _JS.get("scroll_to_bottom", "window.scrollTo(0, document.body.scrollHeight);")
)
JS_PARSE_TRACKS = str(_JS.get("parse_tracks", ""))
JS_UNKASK_URL = str(_JS.get("unkask_url", ""))
JS_EXPAND_BUTTON = str(_JS.get("expand_button", "arguments[0].scrollIntoView({block: 'center'});"))
JS_CLICK = str(_JS.get("click", "arguments[0].click();"))