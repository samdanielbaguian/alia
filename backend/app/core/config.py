from typing import List
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""
    
    # MongoDB Configuration
    MONGODB_URI: str = "mongodb://localhost:27017"
    MONGODB_DB_NAME: str = "alia_db"
    
    # JWT Configuration
    JWT_SECRET_KEY: str
    JWT_ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 1440  # 24 hours
    
    # AliExpress API
    ALIEXPRESS_API_KEY: str = ""
    ALIEXPRESS_API_SECRET: str = ""
    
    # Alibaba API
    ALIBABA_API_KEY: str = ""
    
    # Payment Providers
    ORANGE_MONEY_API_KEY: str = ""
    MOOV_MONEY_API_KEY: str = ""
    WAVE_API_KEY: str = ""
    STRIPE_API_KEY: str = ""
    
    # Application Settings
    BACKEND_CORS_ORIGINS: List[str] = ["http://localhost:3000", "http://localhost:8000"]
    API_V1_PREFIX: str = "/api"
    PROJECT_NAME: str = "Alia"
    BASE_URL: str = "https://alia.com"  # Base URL for share links
    
    model_config = SettingsConfigDict(
        env_file=".env",
        case_sensitive=True,
        extra="ignore"
    )


# Global settings instance
settings = Settings()
