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
    TMDB_READ_TOKEN: Optional[str] = os.getenv("TMDB_READ_TOKEN")
    TMDB_BASE_URL: str = "https://api.themoviedb.org/3"

    # eBay API Configuration
    EBAY_APP_ID: Optional[str] = os.getenv("EBAY_APP_ID")  # Client ID
    EBAY_CERT_ID: Optional[str] = os.getenv("EBAY_CERT_ID")  # Client Secret
    EBAY_API_KEY: Optional[str] = os.getenv("EBAY_API_KEY")  # Legacy support
    EBAY_ENVIRONMENT: str = os.getenv("EBAY_ENVIRONMENT", "production")  # or "sandbox"

    # eBay API Endpoints
    @property
    def EBAY_OAUTH_URL(self) -> str:
        if self.EBAY_ENVIRONMENT == "sandbox":
            return "https://api.sandbox.ebay.com/identity/v1/oauth2/token"
        return "https://api.ebay.com/identity/v1/oauth2/token"

    @property
    def EBAY_BROWSE_API_URL(self) -> str:
        if self.EBAY_ENVIRONMENT == "sandbox":
            return "https://api.sandbox.ebay.com/buy/browse/v1"
        return "https://api.ebay.com/buy/browse/v1"

    # Application settings
    MAX_FILE_SIZE: int = 10 * 1024 * 1024  # 10MB
    ALLOWED_IMAGE_TYPES: list = ["image/jpeg", "image/png", "image/webp"]

settings = Settings()