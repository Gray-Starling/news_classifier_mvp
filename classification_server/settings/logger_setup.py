import logging
from logging.handlers import TimedRotatingFileHandler
import os
from datetime import datetime
from settings.paths import LOGS_DIR_PATH
from settings.env_config import DEPLOY_MODE

class CustomFormatter(logging.Formatter):
    def format(self, record):
        if not hasattr(record, 'process_type') or record.process_type == 'unknown':
            record.process_type = record.name
        return super().format(record)

def setup_logger(name: str) -> logging.Logger:
    LOGGING_LVL = "INFO" if DEPLOY_MODE == "prod" else "DEBUG"
    log_directory = LOGS_DIR_PATH

    os.makedirs(log_directory, exist_ok=True)
    current_date_str = datetime.now().strftime("%Y-%m-%d")

    log_filename = log_directory / f"model_{current_date_str}.log"

    log_format = "%(asctime)s - %(levelname)s - %(process_type)s - %(message)s"
    formatter = CustomFormatter(log_format)

    logger = logging.getLogger(name)
    logger.setLevel(getattr(logging, LOGGING_LVL))

    file_handler = TimedRotatingFileHandler(
        log_filename, when="midnight", backupCount=30, encoding='utf-8'
    )
    file_handler.setFormatter(formatter)

    console_handler = logging.StreamHandler()
    console_handler.setFormatter(formatter)

    if not logger.handlers:
        logger.addHandler(file_handler)
        logger.addHandler(console_handler)

    logger.propagate = False


    return logger

system_logger = setup_logger("system")
system_logger.debug("Логер system инициализирован")
model_logger = setup_logger("model")
system_logger.debug("Логер model инициализирован")
