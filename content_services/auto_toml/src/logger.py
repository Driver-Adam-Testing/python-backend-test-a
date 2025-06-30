import logging
import sys


def _setup_logger(name: str | None = None, level: int = logging.INFO) -> logging.Logger:
    class LogFormatter(logging.Formatter):
        def format(self, record: logging.LogRecord) -> str:
            COLORS = {
                "RESET": "\033[0m",
                "DEBUG": "\033[36m",  # Cyan
                "INFO": "\033[32m",  # Green
                "WARNING": "\033[33m",  # Yellow
                "ERROR": "\033[31m",  # Red
                "CRITICAL": "\033[35m",  # Magenta
            }
            level_name = record.levelname
            color = COLORS.get(level_name, COLORS["RESET"])
            message = super().format(record)
            return f"{color}{message}{COLORS['RESET']}"

    logger = logging.getLogger(name)
    logger.setLevel(level)

    for handler in logger.handlers[:]:
        logger.removeHandler(handler)

    handler = logging.StreamHandler(sys.stdout)
    handler.setLevel(level)

    formatter = LogFormatter("%(message)s")
    handler.setFormatter(formatter)

    logger.addHandler(handler)

    return logger


logger = _setup_logger(__file__, level=logging.DEBUG)
