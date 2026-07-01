import logging
import sys


def setup_logging() -> None:
    # Import inside function to avoid circular import
    from app.core.config import settings

    log_level = logging.DEBUG if settings.ENV == "development" else logging.INFO

    log_format = (
        "%(asctime)s - [%(levelname)s] - "
        "%(name)s - (%(filename)s:%(lineno)d) - %(message)s"
    )

    logging.basicConfig(
        level=log_level,
        format=log_format,
        handlers=[logging.StreamHandler(sys.stdout)]
    )

    # Reduce noise from libraries
    logging.getLogger("sqlalchemy.engine").setLevel(logging.WARNING)
    logging.getLogger("apscheduler").setLevel(logging.WARNING)
    logging.getLogger("uvicorn.error").setLevel(logging.INFO)
    logging.getLogger("uvicorn.access").setLevel(logging.INFO)

    logger = logging.getLogger("app")
    logger.info(
        "Logging configured successfully in %s mode.",
        settings.ENV
    )