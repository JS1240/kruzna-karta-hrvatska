import logging

from app.core.config import settings


def setup_logging() -> None:
    """Configure application logging."""
    level = logging.DEBUG if settings.api.debug else logging.INFO
    
    # Use log format from configuration
    log_format = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    if settings.logging.format == "json":
        # Could implement JSON logging here in the future
        pass
    
    logging.basicConfig(level=level, format=log_format)
    
    # Set log level from configuration
    if settings.logging.level:
        level_mapping = {
            "DEBUG": logging.DEBUG,
            "INFO": logging.INFO,
            "WARNING": logging.WARNING,
            "ERROR": logging.ERROR,
            "CRITICAL": logging.CRITICAL
        }
        level = level_mapping.get(settings.logging.level.upper(), logging.INFO)
        logging.getLogger().setLevel(level)
    
    # Reduce verbosity of external libraries if not debugging
    if not settings.api.debug:
        logging.getLogger("uvicorn").setLevel(logging.WARNING)
        logging.getLogger("uvicorn.error").setLevel(logging.WARNING)
        logging.getLogger("uvicorn.access").setLevel(logging.WARNING)
