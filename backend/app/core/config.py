"""Configuration module using the new Pydantic-based system."""

from app.config.components import get_settings

# For backwards compatibility, expose the settings instance
settings = get_settings()

# Export commonly used settings for backwards compatibility
__all__ = ["settings"]
