from pydantic_settings import BaseSettings
from typing import List

class Settings(BaseSettings):
    # App
    APP_NAME: str = "FileFlow"
    APP_VERSION: str = "1.0.0"
    ENVIRONMENT: str = "production"
    DEBUG: bool = False
    SECRET_KEY: str
    API_V1_PREFIX: str = "/api/v1"
    
    # Server
    HOST: str = "0.0.0.0"
    PORT: int = 8000
    
    # Database
    DATABASE_URL: str
    DATABASE_POOL_SIZE: int = 20
    DATABASE_MAX_OVERFLOW: int = 10
    
    # Redis
    REDIS_URL: str
    REDIS_CACHE_TTL: int = 3600
    
    # JWT
    JWT_SECRET_KEY: str
    JWT_ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    REFRESH_TOKEN_EXPIRE_DAYS: int = 7
    
    # Backblaze B2
    B2_KEY_ID: str | None = None
    B2_APP_KEY: str | None = None
    B2_BUCKET_NAME: str | None = None
    B2_ENDPOINT_URL: str | None = None
    S3_PRESIGNED_URL_EXPIRY: int = 3600  # 1 hour 
    # Elasticsearch
    ELASTICSEARCH_URL: str
    ELASTICSEARCH_INDEX: str = "fileflow_files"
    
    # Celery
    CELERY_BROKER_URL: str
    CELERY_RESULT_BACKEND: str
    
    # Email
    SENDGRID_API_KEY: str = ""
    FROM_EMAIL: str = "noreply@fileflow.com"
    
    # SMS
    TWILIO_ACCOUNT_SID: str = ""
    TWILIO_AUTH_TOKEN: str = ""
    TWILIO_PHONE_NUMBER: str = ""
    
    # Security
    CORS_ORIGINS: List[str] = ["http://localhost:3000"]
    RATE_LIMIT_PER_MINUTE: int = 60
    MAX_FILE_SIZE_MB: int = 100
    
    # Monitoring
    SENTRY_DSN: str = ""
    
    # Storage Quotas
    FREE_STORAGE_GB: int = 5
    PREMIUM_STORAGE_GB: int = 50
    FAMILY_STORAGE_GB: int = 200
    
    class Config:
        env_file = ".env"
        case_sensitive = True

settings = Settings()
