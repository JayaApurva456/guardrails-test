"""Configuration"""
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    GEMINI_API_KEY: str = ""
    DATABASE_URL: str = "postgresql://admin:password@postgres:5432/guardrails"
    REDIS_URL: str = "redis://redis:6379"
    ENVIRONMENT: str = "production"
    LOG_LEVEL: str = "INFO"
    
    class Config:
        env_file = ".env"

settings = Settings()
