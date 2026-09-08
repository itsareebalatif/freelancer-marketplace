# app/core/config.py
from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    DATABASE_URL: str = "postgresql+psycopg://postgres:postgres@localhost:5432/freelancer_db"
    
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

settings = Settings()