import logging

LOG_FILE = "transaction.log"

def setup_logging():
    file_handler = logging.FileHandler(LOG_FILE, encoding="utf-8")
    formatter = logging.Formatter("%(asctime)s [%(levelname)s]: %(message)s")
    file_handler.setFormatter(formatter)

    app_logger = logging.getLogger("app")

    if not any(isinstance(h, logging.FileHandler) for h in app_logger.handlers):
        app_logger.addHandler(file_handler)
        app_logger.setLevel(logging.INFO)

setup_logging()
