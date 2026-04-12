from pydantic import BaseSettings


class Settings(BaseSettings):
    SUPABASE_URL: str
    SUPABASE_ANON_KEY: str
    SUPABASE_SERVICE_KEY: str

    # Queue settings
    QUEUE_HIGH: str = "job_queue:high"
    QUEUE_MED: str = "job_queue:med"
    QUEUE_DEFAULT: str = "job_queue:default"

    # Worker settings
    MIN_WARM_WORKERS: int = 2

    class Config:
        env_file = ".env"


settings = Settings()
