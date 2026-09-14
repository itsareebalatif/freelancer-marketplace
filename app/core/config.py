# app/core/config.py
from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    DATABASE_URL: str = "postgresql+psycopg://postgres:postgres@localhost:5432/freelancer_db"
    JWT_SECRET: str
    JWT_ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    REFRESH_TOKEN_EXPIRE_DAYS: int = 7
    PORT: int = 8000
    COOKIE_SECURE: bool = False
    ENV: str = "development"

    RESEND_API_KEY: str = ""
    EMAIL_FROM_ADDRESS: str = "onboarding@resend.dev"

    SUPABASE_URL: str = ""
    SUPABASE_SERVICE_ROLE_KEY: str = ""
    SUPABASE_STORAGE_BUCKET: str = "marketplace-files"
    SIGNED_URL_EXPIRY_SECONDS: int = 300

    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

settings = Settings()