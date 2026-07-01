import logging
import sys
from app.core.config import settings

def setup_logging() -> None:
    # Use appropriate log levels based on env
    log_level = logging.DEBUG if settings.ENV == "development" else logging.INFO

    # Custom log format
    log_format = "%(asctime)s - [%(levelname)s] - %(name)s - (%(filename)s:%(lineno)d) - %(message)s"

    logging.basicConfig(
        level=log_level,
        format=log_format,
        handlers=[
            logging.StreamHandler(sys.stdout)
        ]
    )

    # Manage noisy external libraries
    logging.getLogger("sqlalchemy.engine").setLevel(logging.WARNING)
    logging.getLogger("apscheduler").setLevel(logging.WARNING)
    logging.getLogger("uvicorn.error").setLevel(logging.INFO)
    logging.getLogger("uvicorn.access").setLevel(logging.INFO)

    logger = logging.getLogger("app")
    logger.info("Logging configured successfully in %s mode.", settings.ENV)
