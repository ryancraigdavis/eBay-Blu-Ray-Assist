import os
from typing import Optional

class Settings:
    # AWS S3 Configuration
    AWS_ACCESS_KEY_ID: Optional[str] = os.getenv("AWS_ACCESS_KEY_ID")
    AWS_SECRET_ACCESS_KEY: Optional[str] = os.getenv("AWS_SECRET_ACCESS_KEY")
    AWS_REGION: str = os.getenv("AWS_REGION", "us-east-1")
    S3_BUCKET_NAME: Optional[str] = os.getenv("S3_BUCKET_NAME")

    # TMDB API Configuration
    TMDB_API_KEY: Optional[str] = os.getenv("TMDB_API_KEY")
    TMDB_BASE_URL: str = "https://api.themoviedb.org/3"

    # Application settings
    MAX_FILE_SIZE: int = 10 * 1024 * 1024  # 10MB
    ALLOWED_IMAGE_TYPES: list = ["image/jpeg", "image/png", "image/webp"]

settings = Settings()