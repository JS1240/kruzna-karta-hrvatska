"""Pydantic configuration components for Kruzna Karta Hrvatska backend."""

import os
import re
from pathlib import Path
from typing import Any, Dict, List, Optional

import yaml
from pydantic import BaseModel, Field, field_validator
from pydantic_settings import BaseSettings


def expand_env_vars(value: Any) -> Any:
    """Recursively expand environment variables in configuration values."""
    if isinstance(value, str):
        # Pattern: ${VAR_NAME:default_value} or ${VAR_NAME}
        pattern = r'\$\{([^}]+)\}'
        
        def replace_env_var(match):
            var_expr = match.group(1)
            if ':' in var_expr:
                var_name, default = var_expr.split(':', 1)
                return os.getenv(var_name, default)
            else:
                return os.getenv(var_expr, '')
        
        return re.sub(pattern, replace_env_var, value)
    elif isinstance(value, dict):
        return {k: expand_env_vars(v) for k, v in value.items()}
    elif isinstance(value, list):
        return [expand_env_vars(item) for item in value]
    else:
        return value


def convert_types(value: Any) -> Any:
    """Convert string values to appropriate Python types."""
    if isinstance(value, str):
        # Convert boolean strings
        if value.lower() in ('true', 'false'):
            return value.lower() == 'true'
        # Convert numeric strings
        if value.isdigit():
            return int(value)
        try:
            if '.' in value:
                return float(value)
        except ValueError:
            pass
    elif isinstance(value, dict):
        return {k: convert_types(v) for k, v in value.items()}
    elif isinstance(value, list):
        return [convert_types(item) for item in value]
    
    return value


class DatabaseConfig(BaseModel):
    """Database configuration."""
    host: str = "localhost"
    port: int = 5432
    name: str = "kruzna_karta_hrvatska"
    user: str = "postgres"
    password: str = ""
    url: Optional[str] = None
    
    # Connection Pool Settings
    pool_size: int = Field(default=5, alias="pool.size")
    pool_max_overflow: int = Field(default=10, alias="pool.max_overflow")
    pool_timeout: int = Field(default=30, alias="pool.timeout")
    pool_recycle: int = Field(default=3600, alias="pool.recycle")
    
    @field_validator('url')
    @classmethod
    def build_database_url(cls, v, info) -> str:
        """Build database URL if not provided."""
        if v and not v.startswith("postgresql://${"):
            return v
        # Build URL from components
        user = info.data.get('user') or 'postgres'
        password = info.data.get('password') or ''
        host = info.data.get('host') or 'localhost'
        port = info.data.get('port') or 5432
        name = info.data.get('name') or 'kruzna_karta_hrvatska'
        
        if password:
            return f"postgresql://{user}:{password}@{host}:{port}/{name}"
        else:
            return f"postgresql://{user}@{host}:{port}/{name}"


class RedisConfig(BaseModel):
    """Redis configuration."""
    host: str = "localhost"
    port: int = 6379
    db: int = 0
    password: Optional[str] = None
    url: Optional[str] = None
    max_connections: int = 20
    
    # Cache Settings
    cache_default_ttl: int = Field(default=300, alias="cache.default_ttl")
    cache_events_ttl: int = Field(default=600, alias="cache.events_ttl")
    cache_search_ttl: int = Field(default=180, alias="cache.search_ttl")
    
    @field_validator('url')
    @classmethod
    def build_redis_url(cls, v, info) -> str:
        """Build Redis URL if not provided."""
        if v:
            return v
        password = info.data.get('password')
        auth = f":{password}@" if password else ""
        host = info.data.get('host') or 'localhost'
        port = info.data.get('port') or 6379
        db = info.data.get('db') or 0
        return f"redis://{auth}{host}:{port}/{db}"


class CacheConfig(BaseModel):
    """Caching configuration."""
    default_ttl: int = 300
    events_ttl: int = 600
    search_ttl: int = 180


class APIConfig(BaseModel):
    """API server configuration."""
    host: str = "0.0.0.0"
    port: int = 8000
    debug: bool = False
    title: str = "Kruzna Karta Hrvatska API"
    version: str = "1.0.0"
    description: str = "Backend API for Croatian Events Platform"
    
    # CORS Settings
    cors_origins: List[str] = Field(default_factory=lambda: ["http://localhost:3000"], alias="cors.origins")
    cors_methods: List[str] = Field(default_factory=lambda: ["GET", "POST", "PUT", "DELETE", "OPTIONS"], alias="cors.methods")
    cors_headers: List[str] = Field(default_factory=lambda: ["*"], alias="cors.headers")
    cors_credentials: bool = Field(default=True, alias="cors.credentials")


class AuthConfig(BaseModel):
    """Authentication configuration."""
    secret_key: str
    algorithm: str = "HS256"
    access_token_expire_minutes: int = 30
    refresh_token_expire_days: int = 7
    
    @field_validator('secret_key')
    @classmethod
    def secret_key_must_be_set(cls, v) -> str:
        if not v:
            # Generate a secure random key if not provided
            import secrets
            import logging
            
            logger = logging.getLogger(__name__)
            secure_key = secrets.token_urlsafe(32)
            
            logger.warning(
                "SECRET_KEY not set! Generated temporary secure key. "
                "For production, set SECRET_KEY environment variable to a secure random string."
            )
            
            return secure_key
            
        # Reject known insecure values
        insecure_values = [
            "your-secret-key-here",
            "secret",
            "development",
            "test",
            "changeme",
            "insecure"
        ]
        
        if v.lower() in insecure_values:
            raise ValueError(f"Secret key '{v}' is insecure. Use a cryptographically secure random string.")
        
        # Enforce minimum length for security
        if len(v) < 16:
            raise ValueError("Secret key must be at least 16 characters long for security.")
            
        return v


class PerformanceConfig(BaseModel):
    """Performance configuration."""
    enable_caching: bool = True
    enable_query_optimization: bool = True
    max_page_size: int = 100
    default_page_size: int = 20


# PaymentConfig removed for MVP (no payment processing)


class ScrapingConfig(BaseModel):
    """Web scraping configuration."""
    # BrightData Settings
    brightdata_user: str = Field(default="demo_user", alias="BRIGHTDATA_USER")
    brightdata_password: str = Field(default="demo_password", alias="BRIGHTDATA_PASSWORD")
    brightdata_host: str = Field(default="brd.superproxy.io", alias="BRIGHTDATA_HOST")
    brightdata_port: int = Field(default=9222, alias="BRIGHTDATA_PORT")
    scraping_browser_url: Optional[str] = Field(default=None, alias="USE_SCRAPING_BROWSER")
    
    # Scraping Settings
    use_proxy: bool = Field(default=True, alias="USE_PROXY")
    use_scraping_browser: bool = Field(default=False, alias="scraping.use_scraping_browser")
    use_playwright: bool = Field(default=True, alias="USE_PLAYWRIGHT")
    enable_scheduler: bool = Field(default=False, alias="ENABLE_SCHEDULER")
    debug_scraper: bool = Field(default=False, alias="DEBUG_SCRAPER")
    max_retries: int = Field(default=3, alias="settings.max_retries")
    timeout: int = Field(default=30, alias="settings.timeout")
    delay_between_requests: float = Field(default=1.0, alias="settings.delay_between_requests")
    
    # Headers
    user_agent: str = Field(
        default="Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36 ScraperBot/1.0",
        alias="headers.user_agent"
    )
    accept: str = Field(
        default="text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
        alias="headers.accept"
    )
    accept_language: str = Field(
        default="en-US,en;q=0.9,hr;q=0.8",
        alias="headers.accept_language"
    )
    
    @property
    def proxy_url(self) -> str:
        """Build proxy URL."""
        return f"http://{self.brightdata_user}:{self.brightdata_password}@{self.brightdata_host}:{self.brightdata_port}"
    
    @property
    def scraping_browser_endpoint(self) -> str:
        """Build scraping browser endpoint."""
        # If we have a direct scraping browser URL (WebSocket), use that
        if self.scraping_browser_url:
            return self.scraping_browser_url
        # Otherwise, build the HTTPS endpoint
        return f"https://{self.brightdata_host}:{self.brightdata_port}"
    
    @property
    def is_websocket_endpoint(self) -> bool:
        """Check if the scraping browser endpoint is a WebSocket URL."""
        return bool(self.scraping_browser_url and self.scraping_browser_url.startswith('wss://'))
    
    @property
    def headers_dict(self) -> Dict[str, str]:
        """Get headers as dictionary."""
        return {
            "User-Agent": self.user_agent,
            "Accept": self.accept,
            "Accept-Language": self.accept_language,
        }


class OpenAIConfig(BaseModel):
    """OpenAI configuration."""
    api_key: Optional[str] = None
    model: str = "gpt-4"
    max_tokens: int = 1000


class GeocodingConfig(BaseModel):
    """Geocoding service configuration."""
    provider: str = "nominatim"
    api_key: Optional[str] = None
    mapbox_token: Optional[str] = Field(default=None, alias="VITE_MAPBOX_ACCESS_TOKEN")


class EmailConfig(BaseModel):
    """Email configuration."""
    smtp_host: Optional[str] = None
    smtp_port: int = 587
    smtp_user: Optional[str] = None
    smtp_password: Optional[str] = None
    from_email: str = "noreply@kruzna-karta.hr"


class ServicesConfig(BaseModel):
    """Third-party services configuration."""
    openai: OpenAIConfig
    geocoding: GeocodingConfig
    email: EmailConfig


class LoggingConfig(BaseModel):
    """Logging configuration."""
    level: str = "INFO"
    format: str = "json"
    file: Optional[str] = None
    max_size: str = "10MB"
    backup_count: int = 5


class MonitoringConfig(BaseModel):
    """Monitoring and observability configuration."""
    enable_metrics: bool = True
    enable_tracing: bool = False
    metrics_port: int = 9090
    health_check_interval: int = 30


class FeatureFlags(BaseModel):
    """Feature flags configuration."""
    enable_analytics: bool = True
    enable_recommendations: bool = True
    enable_social_features: bool = True
    enable_booking: bool = True
    enable_translations: bool = True


class DevelopmentConfig(BaseModel):
    """Development-specific configuration."""
    reload: bool = False
    debug_sql: bool = False
    mock_external_apis: bool = False
    seed_database: bool = False


class Settings(BaseSettings):
    """Main application settings."""
    
    # Core Configuration Components
    database: DatabaseConfig
    redis: RedisConfig
    api: APIConfig
    auth: AuthConfig
    performance: PerformanceConfig
    # payments: PaymentConfig - removed for MVP (no payment processing)
    scraping: ScrapingConfig
    services: ServicesConfig
    logging: LoggingConfig
    monitoring: MonitoringConfig
    features: FeatureFlags
    development: DevelopmentConfig
    
    # Additional Settings for backwards compatibility
    frontend_url: str = "http://localhost:3000"
    third_party_api_keys: Optional[str] = None
    
    class Config:
        env_file = ".env"
        case_sensitive = False
        extra = "ignore"
        
        # Allow population by field name and alias
        populate_by_name = True
        
    @classmethod
    def from_yaml(cls, config_path: Optional[str] = None) -> "Settings":
        """Load settings from YAML file with environment variable expansion."""
        if config_path is None:
            # Default to config.yaml in backend directory
            backend_dir = Path(__file__).parent.parent.parent
            config_path = backend_dir / "config.yaml"
        
        if not Path(config_path).exists():
            raise FileNotFoundError(f"Configuration file not found: {config_path}")
        
        with open(config_path, 'r', encoding='utf-8') as f:
            config_data = yaml.safe_load(f)
        
        # Expand environment variables
        config_data = expand_env_vars(config_data)
        
        # Convert types
        config_data = convert_types(config_data)
        
        return cls(**config_data)
    
    # Convenience properties for backwards compatibility
    @property
    def database_url(self) -> str:
        return self.database.url
    
    @property
    def redis_url(self) -> str:
        return self.redis.url
    
    @property
    def secret_key(self) -> str:
        return self.auth.secret_key
    
    @property
    def algorithm(self) -> str:
        return self.auth.algorithm
    
    @property
    def access_token_expire_minutes(self) -> int:
        return self.auth.access_token_expire_minutes
    
    @property
    def enable_caching(self) -> bool:
        return self.performance.enable_caching
    
    @property
    def enable_query_optimization(self) -> bool:
        return self.performance.enable_query_optimization
    
    @property
    def db_pool_size(self) -> int:
        return self.database.pool_size
    
    @property
    def db_max_overflow(self) -> int:
        return self.database.pool_max_overflow
    
    @property
    def db_pool_timeout(self) -> int:
        return self.database.pool_timeout
    
    @property
    def db_pool_recycle(self) -> int:
        return self.database.pool_recycle


def load_config(config_path: Optional[str] = None) -> Settings:
    """Load configuration from YAML file or environment variables."""
    try:
        return Settings.from_yaml(config_path)
    except FileNotFoundError:
        # Fallback to environment variables only
        return Settings()


# Global configuration instance
settings: Optional[Settings] = None


def get_settings() -> Settings:
    """Get the global settings instance."""
    global settings
    if settings is None:
        settings = load_config()
    return settings