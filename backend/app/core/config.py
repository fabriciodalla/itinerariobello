from functools import lru_cache
from secrets import token_urlsafe

from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    app_name: str = "Controle Itinerario Comercial Bello"
    app_env: str = Field(default="local", alias="APP_ENV")
    app_debug: bool = Field(default=False, alias="APP_DEBUG")
    database_url: str = Field(
        default="postgresql+psycopg://bello:bello_local_password@db:5432/itinerario_bello",
        alias="DATABASE_URL",
    )
    photos_dir: str = Field(default="/app/storage/photos", alias="PHOTOS_DIR")
    cors_origins: str = Field(
        default="http://localhost:3000,http://localhost:5173,http://localhost:8081,http://localhost:19006",
        alias="CORS_ORIGINS",
    )
    secret_key: str = Field(default_factory=lambda: token_urlsafe(32), alias="SECRET_KEY")
    access_token_expire_minutes: int = Field(default=10080, alias="ACCESS_TOKEN_EXPIRE_MINUTES")
    reverse_geocoding_enabled: bool = Field(default=False, alias="REVERSE_GEOCODING_ENABLED")
    reverse_geocoding_provider: str = Field(default="nominatim", alias="REVERSE_GEOCODING_PROVIDER")
    reverse_geocoding_timeout_seconds: float = Field(default=3.0, alias="REVERSE_GEOCODING_TIMEOUT_SECONDS")
    reverse_geocoding_user_agent: str = Field(
        default="itinerario-bello-prototipo/0.1",
        alias="REVERSE_GEOCODING_USER_AGENT",
    )
    nominatim_reverse_url: str = Field(
        default="https://nominatim.openstreetmap.org/reverse",
        alias="NOMINATIM_REVERSE_URL",
    )
    frontend_base_url: str = Field(default="http://localhost:5173", alias="FRONTEND_BASE_URL")
    password_reset_token_expire_minutes: int = Field(default=60, alias="PASSWORD_RESET_TOKEN_EXPIRE_MINUTES")
    smtp_host: str | None = Field(default=None, alias="SMTP_HOST")
    smtp_port: int = Field(default=587, alias="SMTP_PORT")
    smtp_username: str | None = Field(default=None, alias="SMTP_USERNAME")
    smtp_password: str | None = Field(default=None, alias="SMTP_PASSWORD")
    smtp_from_email: str | None = Field(default=None, alias="SMTP_FROM_EMAIL")
    smtp_from_name: str = Field(default="Itinerario Bello", alias="SMTP_FROM_NAME")
    smtp_use_tls: bool = Field(default=True, alias="SMTP_USE_TLS")
    smtp_use_ssl: bool = Field(default=False, alias="SMTP_USE_SSL")
    smtp_timeout_seconds: float = Field(default=10.0, alias="SMTP_TIMEOUT_SECONDS")
    cookie_secure: bool = Field(default=False, alias="COOKIE_SECURE")
    cookie_domain: str | None = Field(default=None, alias="COOKIE_DOMAIN")
    app_timezone: str = Field(default="America/Cuiaba", alias="APP_TIMEZONE")

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    @property
    def cors_origin_list(self) -> list[str]:
        return [origin.strip() for origin in self.cors_origins.split(",") if origin.strip()]

    @property
    def smtp_configured(self) -> bool:
        return bool(self.smtp_host and (self.smtp_from_email or self.smtp_username))

    @field_validator("secret_key", mode="before")
    @classmethod
    def default_secret_key_when_blank(cls, value: object) -> str:
        if isinstance(value, str) and value.strip():
            return value
        return token_urlsafe(32)

    @field_validator("reverse_geocoding_provider", mode="before")
    @classmethod
    def normalize_reverse_geocoding_provider(cls, value: object) -> str:
        if isinstance(value, str) and value.strip():
            return value.strip().lower()
        return "nominatim"

    @field_validator(
        "smtp_host",
        "smtp_username",
        "smtp_password",
        "smtp_from_email",
        mode="before",
    )
    @classmethod
    def none_when_blank(cls, value: object) -> str | None:
        if isinstance(value, str):
            cleaned = value.strip()
            return cleaned or None
        return value


@lru_cache
def get_settings() -> Settings:
    return Settings()
