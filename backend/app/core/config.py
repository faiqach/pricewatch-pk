"""Application configuration loaded from environment variables."""

from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    app_name: str = "PriceWatch PK"
    app_version: str = "1.0.0"
    debug: bool = True
    environment: str = "development"

    host: str = "0.0.0.0"
    port: int = 8000

    database_url: str = "postgresql://USERNAME:PASSWORD@localhost:5432/pricewatch_pk"

    secret_key: str = "your-secret-key-minimum-32-characters-long"
    algorithm: str = "HS256"
    access_token_expire_minutes: int = 1440

    bcrypt_salt_rounds: int = 12

    openrouter_api_key: str = "sk-or-v1-your-key-here"
    ai_default_model: str = "google/gemini-flash-1.5"
    ai_fallback_model: str = "x-ai/grok-beta"

    scraper_run_time: str = "06:00"
    scraper_retry_attempts: int = 3
    scraper_retry_delay_minutes: int = 10

    tesseract_cmd: str = "/usr/bin/tesseract"
    ocr_temp_dir: str = "./temp/ocr"

    rate_limit_per_minute: int = 100

    anomaly_threshold_percent: float = 15.0
    zscore_threshold: float = 2.0

    bahawalnagar_portal_url: str = ""
    lahore_portal_url: str = ""
    multan_portal_url: str = ""
    bahawalpur_portal_url: str = ""
    islamabad_portal_url: str = ""

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"


settings = Settings()
