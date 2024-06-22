import logging
from logging import StreamHandler
from logging.handlers import RotatingFileHandler


def setup_logging():
    """Set up logging."""
    logging.basicConfig(
        handlers=[
            RotatingFileHandler("train.log", maxBytes=32 * 1024 * 1024, backupCount=5),
            StreamHandler(),
        ],
        level=logging.INFO,
        format="[%(asctime)s] [%(levelname)-7s] [%(name)s]: %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )
