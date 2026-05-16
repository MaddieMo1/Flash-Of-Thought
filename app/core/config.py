from pydantic_settings import BaseSettings
from functools import lru_cache
from typing import Optional

class Settings(BaseSettings):
    # App
    APP_NAME: str = "FlashOfThought"
    
    # OSS
    STORAGE_PROVIDER: str = "oss"
    OSS_ENDPOINT: str
    OSS_BUCKET_AUDIO: str
    OSS_ACCESS_KEY_ID: str
    OSS_ACCESS_KEY_SECRET: str
    OSS_PUBLIC_BASE_URL: Optional[str] = None
    OSS_USE_SIGNED_URL: bool = True
    OSS_SIGNED_URL_EXPIRE_SEC: int = 3600
    
    # Qwen / DashScope
    DASHSCOPE_API_KEY: str
    QWEN_CHAT_MODEL: str = "qwen-plus"
    QWEN_EMBED_MODEL: str = "text-embedding-v4"
    QWEN_ASR_MODEL: str = "qwen3-asr-flash"
    
    # Vector DB
    CHROMA_DB_PATH: str = "./data/chroma_db"

    # Auth
    JWT_SECRET_KEY: str = "change-this-development-secret"
    JWT_ALGORITHM: str = "HS256"
    JWT_ACCESS_TOKEN_EXPIRE_MINUTES: int = 10080
    USERS_DB_PATH: str = "./data/users.sqlite3"
    
    class Config:
        env_file = ".env"
        extra = "ignore"  # Ignore extra fields in .env

@lru_cache()
def get_settings():
    return Settings()
