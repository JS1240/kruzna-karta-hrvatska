import logging
from .core.config import settings

def configure_logging():
    """Configure logging level and format."""
    level = logging.DEBUG if getattr(settings, "debug", False) else logging.INFO
    logging.basicConfig(
        level=level,
        format="%(asctime)s %(levelname)s %(name)s: %(message)s"
    )


