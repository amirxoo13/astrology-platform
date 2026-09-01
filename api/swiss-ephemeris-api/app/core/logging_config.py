import sys
from pathlib import Path

from loguru import logger
from app.core.config import settings


LOGURU_FORMAT = (
    "<green>{time:YYYY-MM-DD HH:mm:ss.SSS}</green> | "
    "<level>{level: <8}</level> | "
    "<cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> | "
    "<level>{message}</level>"
)

# Rotation: 10 MB per file, keep 5 backups
_ROTATION = "10 MB"
_RETENTION = 5
_COMPRESSION = "zip"  # compress old logs

_LOG_DIR = Path("logs")
_LOG_ALL = _LOG_DIR / "api.log"
_LOG_ERRORS = _LOG_DIR / "api-errors.log"


def setup_logging() -> None:
    """Configure loguru for the application.

    Console:
      - DEBUG/INFO: colored, human-readable format
      - WARNING+: JSON per line (serialize=True)

    Files (logs/):
      - api.log:        all levels, rotation 10 MB / 5 backups
      - api-errors.log: WARNING+ only, rotation 10 MB / 5 backups
    """
    _LOG_DIR.mkdir(exist_ok=True)
    logger.remove()

    if settings.log_level in ("DEBUG", "INFO"):
        # Human-readable console
        logger.add(
            sys.stderr,
            format=LOGURU_FORMAT,
            level=settings.log_level,
            colorize=True,
        )
        console_level = settings.log_level
    else:
        # JSON console
        logger.add(
            sys.stderr,
            level=settings.log_level,
            serialize=True,
        )
        console_level = "WARNING"

    # All logs → api.log
    logger.add(
        _LOG_ALL,
        level="DEBUG",
        rotation=_ROTATION,
        retention=_RETENTION,
        compression=_COMPRESSION,
        format="{time:YYYY-MM-DD HH:mm:ss.SSS} | {level: <8} | {name}:{function}:{line} | {message} | {extra}",
        backtrace=True,
    )

    # Errors only → api-errors.log
    logger.add(
        _LOG_ERRORS,
        level="WARNING",
        rotation=_ROTATION,
        retention=_RETENTION,
        compression=_COMPRESSION,
        format="{time:YYYY-MM-DD HH:mm:ss.SSS} | {level: <8} | {name}:{function}:{line} | {message} | {extra}",
        backtrace=True,
    )

    # Silence uvicorn noise
    import logging
    logging.getLogger("uvicorn.access").setLevel(logging.WARNING)
    logging.getLogger("uvicorn.error").setLevel(logging.INFO)


# Shared application logger — import this everywhere
app_logger = logger.bind(name="swiss-ephemeris-api")
