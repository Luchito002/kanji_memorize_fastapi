import logging
import os
from enum import StrEnum
from logging.handlers import TimedRotatingFileHandler
from datetime import datetime

LOG_FORMAT_DEBUG = "%(levelname)s:%(message)s:%(pathname)s:%(funcName)s:%(lineno)d"
LOG_FORMAT_DEFAULT = "%(asctime)s - %(levelname)s - %(name)s - %(message)s"

class LogLevels(StrEnum):
    info = "INFO"
    warn = "WARNING"
    error = "ERROR"
    debug = "DEBUG"

def configure_logging(log_level: str = LogLevels.error):
    log_level = str(log_level).upper()

    log_dir = "/mnt/c/grafana/promtail/logs/KanjiMemorize"
    os.makedirs(log_dir, exist_ok=True)

    logger = logging.getLogger()
    logger.setLevel(getattr(logging, log_level, logging.ERROR))

    formatter = logging.Formatter(
        LOG_FORMAT_DEBUG if log_level == "DEBUG" else LOG_FORMAT_DEFAULT
    )

    today = datetime.now().strftime("%Y-%m-%d")
    log_file = f"{log_dir}/{today}.log"

    file_handler = TimedRotatingFileHandler(
        filename=log_file,
        when="midnight",
        interval=1,
        backupCount=30,
        encoding="utf-8"
    )

    file_handler.setFormatter(formatter)

    console_handler = logging.StreamHandler()
    console_handler.setFormatter(formatter)

    logger.handlers.clear()
    logger.addHandler(file_handler)
    logger.addHandler(console_handler)

    logging.getLogger("uvicorn.access").handlers = logger.handlers
    logging.getLogger("uvicorn.error").handlers = logger.handlers
