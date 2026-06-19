from functools import lru_cache
from secrets import token_urlsafe

from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    app_name: str = "Controle Itinerario Comercial Bello"
    app_env: str = Field(default="local", alias="APP_ENV")
    app_debug: bool = Field(default=True, alias="APP_DEBUG")
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

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    @property
    def cors_origin_list(self) -> list[str]:
        return [origin.strip() for origin in self.cors_origins.split(",") if origin.strip()]

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


@lru_cache
def get_settings() -> Settings:
    return Settings()
