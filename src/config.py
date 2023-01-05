import configparser
import datetime
import logging
from functools import lru_cache
from logging.handlers import RotatingFileHandler
from pathlib import Path

BASE_DIR = Path(__file__).parent.parent.resolve()
# Set up the logger
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)

# Create a file handler to write the log to a file
handler = RotatingFileHandler(
    BASE_DIR / "logs" / "main.log", "w", maxBytes=10000, backupCount=5, encoding="utf-8"
)
handler.setLevel(logging.INFO)

# Create a formatter for the log messages
formatter = logging.Formatter("%(asctime)s - %(name)s - %(levelname)s - %(message)s")
handler.setFormatter(formatter)

# Add the handler to the logger
logger.addHandler(handler)


@lru_cache
def get_config():

    config = configparser.ConfigParser()
    try:
        data = config.read(
            Path(__file__).parent.parent.resolve() / "config.ini", encoding="utf-8"
        )

        if len(data) == 0:
            raise FileNotFoundError("Failed to open")

        if config.has_section("Default"):
            return {k: v for k, v in config["Default"].items()}
        else:
            logger.exception("Failed to find Default section in config.ini")
            raise Exception("No default section in config.ini")

    except AssertionError:
        logger.exception("Failed to read config.ini")
        raise Exception("Invaild INI path")
    except FileNotFoundError:
        logger.exception("Failed to open config.ini")
        raise Exception("INI File not found")


@lru_cache
def get_previous_day() -> str:
    return (datetime.datetime.now() - datetime.timedelta(days=1)).date().isoformat()
