# core/logger.py
import logging
import os
from config import LOGS_DIR


def setup_logger(step_name):
    """Sets up a logger that writes to both console and a specific file."""
    os.makedirs(LOGS_DIR, exist_ok=True)

    logger = logging.getLogger(step_name)
    logger.setLevel(logging.INFO)

    # Avoid duplicate handlers if instantiated multiple times
    if not logger.handlers:
        formatter = logging.Formatter('%(asctime)s | %(levelname)s | %(message)s', datefmt='%Y-%m-%d %H:%M:%S')

        # File Handler
        fh = logging.FileHandler(os.path.join(LOGS_DIR, f"{step_name}.log"), mode='w', encoding="utf-8")
        fh.setFormatter(formatter)

        # Console Handler
        ch = logging.StreamHandler()
        ch.setFormatter(formatter)

        logger.addHandler(fh)
        logger.addHandler(ch)

    return logger