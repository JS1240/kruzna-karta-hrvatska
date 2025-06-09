from pathlib import Path
from pydantic_settings import BaseSettings
from typing import Optional


class Settings(BaseSettings):
    # Database settings
    database_url: str
    db_host: str = "localhost"
    db_port: int = 5432
    db_name: str = "kruzna_karta_hrvatska"
    db_user: str = "postgres"
    db_password: str = ""

    # API settings
    api_host: str = "0.0.0.0"
    api_port: int = 8000
    debug: bool = False

    # CORS settings
    frontend_url: str = "http://localhost:5173"

    # JWT settings
    secret_key: str
    algorithm: str = "HS256"
    access_token_expire_minutes: int = 30

    # Scraping settings
    enable_scheduler: bool = False
    use_proxy: bool = False
    use_playwright: bool = True
    use_scraping_browser: bool = False
    brightdata_user: Optional[str] = None
    brightdata_password: Optional[str] = None
    brightdata_port: int = 22225
    category_url: str = "https://www.entrio.hr/hr/"

    class Config:
        env_file = Path(__file__).resolve().parents[2] / ".env"
        case_sensitive = False


settings = Settings()


def validate_settings(cfg: Settings) -> None:
    """Validate critical configuration values."""
    if cfg.use_proxy and (not cfg.brightdata_user or not cfg.brightdata_password):
        raise ValueError(
            "USE_PROXY requires BRIGHTDATA_USER and BRIGHTDATA_PASSWORD to be set"
        )


validate_settings(settings)
