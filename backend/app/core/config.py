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

    class Config:
        env_file = ".env"
        case_sensitive = False


settings = Settings()