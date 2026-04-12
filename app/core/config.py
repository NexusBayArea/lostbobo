from app.core.bootstrap import bootstrap

bootstrap()
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    # Normalized Infrastructure Variables
    APP_URL: str
    DATA_URL: str = ""  # Default empty if not provided by infra

    JWT_SECRET: str
    JWT_AUDIENCE: str = "authenticated"
    PUBLIC_KEY: str = ""
    SECRET_KEY: str

    API_TOKEN: str

    # Queue settings
    QUEUE_HIGH: str = "job_queue:high"
    QUEUE_MED: str = "job_queue:med"
    QUEUE_DEFAULT: str = "job_queue:default"

    # Worker settings
    MIN_WARM_WORKERS: int = 2

    # Redis Connectivity
    REDIS_URL: str = "redis://localhost:6379/0"

    model_config = SettingsConfigDict(env_file=".env", extra="ignore")


settings = Settings()
