import logging
import os
from logging.handlers import RotatingFileHandler

LOG_DIR = "/app/logs"
LOG_FILE = os.path.join(LOG_DIR, "transaction.log")


def setup_logging():
    """
    Конфигурирует систему логирования приложения.

    Особенности:
    1) Использует RotatingFileHandler для предотвращения переполнения диска (max 10MB, 5 бэкапов).
    2) Формат логов включает временную метку, уровень важности и PID процесса (полезно для отладки в Docker).
    3) Реализован fallback: если прав на запись в директорию /app/logs нет, вывод переключается в консоль (stdout).
    """
    if not os.path.exists(LOG_DIR):
        try:
            os.makedirs(LOG_DIR)
        except PermissionError:
            pass
    try:
        file_handler = RotatingFileHandler(
            LOG_FILE, maxBytes=10485760, backupCount=5, encoding="utf-8"
        )
        formatter = logging.Formatter(
            "%(asctime)s [%(levelname)s] [PID:%(process)d]: %(message)s"
        )

        file_handler.setFormatter(formatter)
        root_logger = logging.getLogger()
        if not any(isinstance(h, RotatingFileHandler) for h in root_logger.handlers):
            root_logger.addHandler(file_handler)
            root_logger.setLevel(logging.INFO)
    except PermissionError:
        logging.basicConfig(level=logging.INFO)
        logging.getLogger("app").warning(
            "Permission denied for log file. Using console."
        )


setup_logging()
