"""Application configuration."""

from pydantic_settings import BaseSettings
from typing import Optional
import os
from pathlib import Path


class Settings(BaseSettings):
    """Application settings."""

    # Application
    APP_NAME: str = "TLDRify"
    APP_VERSION: str = "0.1.0"
    DEBUG: bool = True

    # Database
    DATABASE_URL: str = os.getenv(
        "DATABASE_URL",
        "postgresql+psycopg://tldrify_user:tldrify_pass_2024@localhost:5432/tldrify_db"
    )

    # Redis
    REDIS_URL: str = os.getenv("REDIS_URL", "redis://localhost:6379/0")

    # File Upload
    MAX_FILE_SIZE: int = 104857600  # 100MB in bytes
    CHUNK_SIZE: int = 1048576  # 1MB chunks
    UPLOAD_PATH: Path = Path("./uploads")

    @property
    def ALLOWED_EXTENSIONS(self) -> set:
        return {".pdf"}

    # Temporary chunk storage
    TEMP_PATH: Path = Path("./temp_chunks")

    # Security
    SECRET_KEY: str = os.getenv("SECRET_KEY", "your-secret-key-here-change-in-production")
    JWT_SECRET_KEY: str = os.getenv("JWT_SECRET_KEY", "your-jwt-secret-key-here")
    JWT_ALGORITHM: str = "HS256"
    JWT_EXPIRATION_HOURS: int = 24

    # API Keys
    OPENAI_API_KEY: Optional[str] = os.getenv("OPENAI_API_KEY")
    ANTHROPIC_API_KEY: Optional[str] = os.getenv("ANTHROPIC_API_KEY")

    # Qdrant
    QDRANT_HOST: str = os.getenv("QDRANT_HOST", "localhost")
    QDRANT_PORT: int = int(os.getenv("QDRANT_PORT", 6333))
    QDRANT_GRPC_PORT: int = int(os.getenv("QDRANT_GRPC_PORT", 6334))
    QDRANT_API_KEY: Optional[str] = os.getenv("QDRANT_API_KEY")
    QDRANT_COLLECTION_NAME: str = os.getenv("QDRANT_COLLECTION_NAME", "tldrify_vectors")

    # WebSocket
    WS_MESSAGE_QUEUE_SIZE: int = 100

    class Config:
        env_file = ".env"
        case_sensitive = True
        extra = "ignore"  # Ignore extra environment variables


settings = Settings()

# Create directories if they don't exist
settings.UPLOAD_PATH.mkdir(parents=True, exist_ok=True)
settings.TEMP_PATH.mkdir(parents=True, exist_ok=True)