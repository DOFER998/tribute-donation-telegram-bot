import sys

from loguru import logger


def setup_logging(debug: bool = False) -> None:
    logger.remove()
    level = 'DEBUG' if debug else 'INFO'
    logger.add(
        sys.stderr,
        level=level,
        format='<green>{time:YYYY-MM-DD HH:mm:ss.SSS}</green> | '
        '<level>{level: <8}</level> | '
        '<cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> - <level>{message}</level>',
    )
