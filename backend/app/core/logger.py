import logging
import sys

# TODO this should be deprecated in favor of the logger that as of today lives in main.py.
logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)
c_handler = logging.StreamHandler(sys.stdout)
c_handler.setLevel(logging.WARNING)
c_format = logging.Formatter(
    "%(asctime)s - %(name)s - %(levelname)s - %(message)s", datefmt="%Y-%m-%d %H:%M:%S"
)
c_handler.setFormatter(c_format)
logger.addHandler(c_handler)
