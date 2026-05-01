"""
Logger configurable pour alternance-finder.
"""

import logging
import os
import sys
from pathlib import Path


def setup_logger(
    name: str = "alternance-finder",
    log_file: str | None = None,
    level: int = logging.INFO,
) -> logging.Logger:
    """Configure et retourne un logger."""
    logger = logging.getLogger(name)

    if logger.handlers:
        return logger

    logger.setLevel(level)
    formatter = logging.Formatter(
        "%(asctime)s | %(levelname)-8s | %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )

    # Console handler (UTF-8 safe for Windows)
    import io
    utf8_stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
    console = logging.StreamHandler(utf8_stdout)
    console.setLevel(level)
    console.setFormatter(formatter)
    logger.addHandler(console)

    # File handler (optionnel)
    if log_file:
        Path(os.path.dirname(log_file)).mkdir(parents=True, exist_ok=True)
        file_handler = logging.FileHandler(log_file, encoding="utf-8")
        file_handler.setLevel(level)
        file_handler.setFormatter(formatter)
        logger.addHandler(file_handler)

    return logger


# Logger par défaut
logger = setup_logger()
