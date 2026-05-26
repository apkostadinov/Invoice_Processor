import logging
import sys
import os


def setup_logging():

    log_level = os.getenv("LOG_LEVEL", "INFO").upper()
    resolved_level = getattr(logging, log_level, logging.INFO)

    logging.basicConfig(
        level=resolved_level,
        format="%(asctime)s | %(levelname)s | %(name)s | %(message)s",
        handlers=[
            logging.StreamHandler(sys.stdout)
        ],
    )
