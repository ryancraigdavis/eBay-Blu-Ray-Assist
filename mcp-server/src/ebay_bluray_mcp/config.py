"""Configuration and defaults for eBay Blu-ray MCP server.

Secrets are loaded from environment variables (via Doppler).
"""

import os
from dataclasses import dataclass, field
from typing import Optional


@dataclass
class ListingDefaults:
    """Default values for eBay listings."""

    # Item details
    condition: str = "Very Good"
    condition_id: str = "4000"
    location: str = "Los Angeles, CA"
    region_code: str = "A"  # Region A/1 for Americas
    language: str = "English"
    case_type: str = "Standard Blu-ray Case"
    format: str = "Blu-ray"

    # Listing settings
    listing_format: str = "FixedPriceItem"
    duration: str = "GTC"  # Good Till Cancelled (30 days auto-renew)
    best_offer_enabled: bool = False
    quantity: int = 1

    # Shipping
    shipping_service: str = "USPSMedia"
    shipping_cost: str = "4.00"
    dispatch_time_max: str = "2"  # 2 business days

    # Returns
    returns_accepted: str = "ReturnsAccepted"
    returns_within: str = "Days_30"
    refund_option: str = "MoneyBack"
    return_shipping_paid_by: str = "Buyer"

    # Category
    category_id: str = "617"  # DVDs & Blu-ray Discs


@dataclass
class AWSConfig:
    """AWS S3 configuration from environment."""

    access_key_id: str = field(default_factory=lambda: os.environ.get("AWS_ACCESS_KEY_ID", ""))
    secret_access_key: str = field(default_factory=lambda: os.environ.get("AWS_SECRET_ACCESS_KEY", ""))
    region: str = field(default_factory=lambda: os.environ.get("AWS_REGION", "us-east-1"))
    bucket_name: str = field(default_factory=lambda: os.environ.get("S3_BUCKET_NAME", ""))

    def is_configured(self) -> bool:
        return bool(self.access_key_id and self.secret_access_key and self.bucket_name)


@dataclass
class TMDBConfig:
    """TMDB API configuration from environment."""

    api_key: str = field(default_factory=lambda: os.environ.get("TMDB_API_KEY", ""))
    read_token: str = field(default_factory=lambda: os.environ.get("TMDB_READ_TOKEN", ""))
    base_url: str = "https://api.themoviedb.org/3"

    def is_configured(self) -> bool:
        return bool(self.read_token)


@dataclass
class ServerConfig:
    """Overall server configuration."""

    # Paths (relative to mcp-server directory)
    images_folder: str = "images"
    template_folder: str = "../backend/src/ebay_movie_assist/template"

    # Config objects
    defaults: ListingDefaults = field(default_factory=ListingDefaults)
    aws: AWSConfig = field(default_factory=AWSConfig)
    tmdb: TMDBConfig = field(default_factory=TMDBConfig)

    def get_images_path(self, base_path: str) -> str:
        """Get absolute path to images folder."""
        return os.path.join(base_path, self.images_folder)

    def get_template_path(self, base_path: str) -> str:
        """Get absolute path to template folder."""
        return os.path.normpath(os.path.join(base_path, self.template_folder))


# Global config instance
config = ServerConfig()
