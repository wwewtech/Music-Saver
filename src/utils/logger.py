import logging
import os
from src.config import LOG_PATH


def setup_logger():
    # Ensure directory exists
    os.makedirs(os.path.dirname(LOG_PATH), exist_ok=True)

    logger = logging.getLogger("VKMusicSaver")
    logger.setLevel(logging.DEBUG)

    # File Handler
    file_handler = logging.FileHandler(LOG_PATH, encoding="utf-8")
    file_formatter = logging.Formatter("%(asctime)s - [%(levelname)s] - %(name)s - %(message)s")
    file_handler.setFormatter(file_formatter)
    file_handler.setLevel(logging.DEBUG)

    # Console Handler
    console_handler = logging.StreamHandler()
    console_handler.setFormatter(file_formatter)
    console_handler.setLevel(logging.INFO) # Keep console cleaner, but file detailed

    logger.addHandler(file_handler)
    logger.addHandler(console_handler)

    return logger


logger = setup_logger()
