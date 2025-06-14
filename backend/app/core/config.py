from typing import Optional

from pydantic_settings import BaseSettings


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

    # Redis settings
    redis_url: Optional[str] = None
    redis_host: str = "localhost"
    redis_port: int = 6379
    redis_db: int = 0
    redis_password: Optional[str] = None
    redis_max_connections: int = 20

    # Performance settings
    enable_caching: bool = True
    enable_query_optimization: bool = True
    db_pool_size: int = 5
    db_max_overflow: int = 10
    db_pool_timeout: int = 30
    db_pool_recycle: int = 3600

    # Stripe payment settings
    stripe_publishable_key: Optional[str] = None
    stripe_secret_key: Optional[str] = None
    stripe_webhook_secret: Optional[str] = None
    stripe_connect_client_id: Optional[str] = (
        None  # For future Stripe Connect integration
    )

    # Payment settings
    platform_commission_rate: float = 5.0  # Default 5% commission
    currency: str = "EUR"
    payment_methods: list[str] = ["card", "sepa_debit"]  # Supported payment methods

    # Third-party API keys (comma separated)
    third_party_api_keys: Optional[str] = None

    class Config:
        env_file = ".env"
        case_sensitive = False
        extra = "ignore"  # Ignore extra fields from .env


settings = Settings()
