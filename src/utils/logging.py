import logging
from pathlib import Path
from typing import Optional


def setup_logging(level: int = logging.INFO, log_file: Optional[Path] = None) -> logging.Logger:
    logger = logging.getLogger("hdbscan_new")
    logger.setLevel(level)
    logger.propagate = False  # avoid duplicate logs

    if logger.handlers:
        return logger  # already configured

    fmt = logging.Formatter("%(asctime)s | %(levelname)s | %(message)s")

    ch = logging.StreamHandler()
    ch.setLevel(level)
    ch.setFormatter(fmt)
    logger.addHandler(ch)

    if log_file is not None:
        log_file.parent.mkdir(parents=True, exist_ok=True)
        fh = logging.FileHandler(log_file, encoding="utf-8")
        fh.setLevel(level)
        fh.setFormatter(fmt)
        logger.addHandler(fh)

    return logger
