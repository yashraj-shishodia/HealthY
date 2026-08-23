from pydantic_settings import BaseSettings, SettingsConfigDict
from typing import Optional


class Settings(BaseSettings):
    PROJECT_NAME: str = "Healthcare Appointment Manager"
    ENVIRONMENT: str = "development"
    
    # Database
    DATABASE_URL: str = "postgresql+asyncpg://healthy_user:healthy_password@localhost:5432/healthy_db"
    
    # Redis & Celery
    REDIS_URL: str = "redis://localhost:6379/0"
    CELERY_BROKER_URL: str = "redis://localhost:6379/0"
    CELERY_RESULT_BACKEND: str = "redis://localhost:6379/0"
    
    # Auth
    JWT_SECRET: str = "super_secret_jwt_key_change_in_production_123456789"
    JWT_ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 24  # 24 hours
    
    # Integrations
    LLM_PROVIDER: str = "mock"  # mock, openai, gemini, anthropic
    LLM_API_KEY: Optional[str] = None
    LLM_MODEL_NAME: str = "gpt-4o-mini"
    
    EMAIL_PROVIDER: str = "mock"  # mock, sendgrid, smtp
    EMAIL_API_KEY: Optional[str] = None
    EMAIL_FROM: str = "noreply@healthyapp.com"
    
    GOOGLE_CLIENT_ID: Optional[str] = None
    GOOGLE_CLIENT_SECRET: Optional[str] = None
    GOOGLE_REDIRECT_URI: str = "http://localhost:5173/calendar/callback"
    
    FRONTEND_URL: str = "http://localhost:5173"

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")


settings = Settings()
