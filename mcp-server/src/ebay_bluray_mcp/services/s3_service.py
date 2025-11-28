"""S3 upload service for Blu-ray images."""

import os
import uuid
from io import BytesIO
from typing import Optional

import boto3
from PIL import Image

from ..config import config


class S3Service:
    """Handle image uploads to AWS S3."""

    def __init__(self):
        self._client = None

    @property
    def client(self):
        """Lazy-load S3 client."""
        if self._client is None:
            if not config.aws.is_configured():
                raise ValueError("AWS credentials not configured. Check Doppler environment.")
            self._client = boto3.client(
                "s3",
                aws_access_key_id=config.aws.access_key_id,
                aws_secret_access_key=config.aws.secret_access_key,
                region_name=config.aws.region,
            )
        return self._client

    def optimize_image(self, image_path: str, max_size: int = 1600) -> BytesIO:
        """Optimize image for web: resize and convert to JPEG."""
        with Image.open(image_path) as img:
            # Convert to RGB if necessary (for PNG with transparency)
            if img.mode in ("RGBA", "P"):
                img = img.convert("RGB")

            # Resize if larger than max_size
            if max(img.size) > max_size:
                img.thumbnail((max_size, max_size), Image.Resampling.LANCZOS)

            # Save to buffer as JPEG
            buffer = BytesIO()
            img.save(buffer, format="JPEG", quality=85, optimize=True)
            buffer.seek(0)
            return buffer

    def upload_image(self, image_path: str) -> str:
        """Upload image to S3 and return public URL.

        Args:
            image_path: Local path to the image file

        Returns:
            Public S3 URL for the uploaded image
        """
        if not os.path.exists(image_path):
            raise FileNotFoundError(f"Image not found: {image_path}")

        # Generate unique filename
        original_name = os.path.basename(image_path)
        name_without_ext = os.path.splitext(original_name)[0]
        # Clean filename
        clean_name = "".join(c if c.isalnum() or c in "-_" else "_" for c in name_without_ext)
        unique_id = str(uuid.uuid4())[:8]
        s3_key = f"bluray-images/{unique_id}-{clean_name}.jpg"

        # Optimize image
        optimized = self.optimize_image(image_path)

        # Upload to S3
        self.client.upload_fileobj(
            optimized,
            config.aws.bucket_name,
            s3_key,
            ExtraArgs={
                "ContentType": "image/jpeg",
                "ACL": "public-read",
            },
        )

        # Construct public URL
        url = f"https://{config.aws.bucket_name}.s3.{config.aws.region}.amazonaws.com/{s3_key}"
        return url


# Singleton instance
s3_service = S3Service()
