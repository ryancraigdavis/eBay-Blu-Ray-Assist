import boto3
import uuid
from typing import Optional
from botocore.exceptions import ClientError, NoCredentialsError
from PIL import Image
import io
from ..config import settings
from ..models import UploadResponse

class S3Service:
    def __init__(self):
        if not all([settings.AWS_ACCESS_KEY_ID, settings.AWS_SECRET_ACCESS_KEY, settings.S3_BUCKET_NAME]):
            raise ValueError("AWS credentials and S3 bucket name must be configured")

        self.s3_client = boto3.client(
            's3',
            aws_access_key_id=settings.AWS_ACCESS_KEY_ID,
            aws_secret_access_key=settings.AWS_SECRET_ACCESS_KEY,
            region_name=settings.AWS_REGION
        )
        self.bucket_name = settings.S3_BUCKET_NAME

    def optimize_image(self, image_data: bytes, max_size: int = 1024) -> bytes:
        """Optimize image for web display"""
        try:
            image = Image.open(io.BytesIO(image_data))

            # Convert to RGB if necessary
            if image.mode in ('RGBA', 'P'):
                image = image.convert('RGB')

            # Resize if too large
            if max(image.size) > max_size:
                image.thumbnail((max_size, max_size), Image.Resampling.LANCZOS)

            # Save optimized image
            output = io.BytesIO()
            image.save(output, format='JPEG', quality=85, optimize=True)
            return output.getvalue()
        except Exception as e:
            raise ValueError(f"Failed to optimize image: {str(e)}")

    async def upload_image(self,
                          file_content: bytes,
                          filename: str,
                          content_type: str,
                          optimize: bool = True) -> UploadResponse:
        """Upload image to S3 bucket"""
        try:
            # Generate unique filename
            file_extension = filename.split('.')[-1] if '.' in filename else 'jpg'
            unique_filename = f"bluray-images/{uuid.uuid4()}.{file_extension}"

            # Optimize image if requested
            if optimize and content_type.startswith('image/'):
                file_content = self.optimize_image(file_content)
                content_type = 'image/jpeg'

            # Upload to S3
            self.s3_client.put_object(
                Bucket=self.bucket_name,
                Key=unique_filename,
                Body=file_content,
                ContentType=content_type,
                ACL='public-read'  # Make images publicly accessible
            )

            # Generate public URL
            s3_url = f"https://{self.bucket_name}.s3.{settings.AWS_REGION}.amazonaws.com/{unique_filename}"

            return UploadResponse(
                filename=unique_filename,
                s3_url=s3_url,
                size=len(file_content),
                content_type=content_type
            )

        except NoCredentialsError:
            raise ValueError("AWS credentials not found")
        except ClientError as e:
            raise ValueError(f"Failed to upload to S3: {str(e)}")
        except Exception as e:
            raise ValueError(f"Upload failed: {str(e)}")

    def delete_image(self, s3_key: str) -> bool:
        """Delete image from S3 bucket"""
        try:
            self.s3_client.delete_object(Bucket=self.bucket_name, Key=s3_key)
            return True
        except Exception:
            return False

s3_service = S3Service() if all([settings.AWS_ACCESS_KEY_ID, settings.AWS_SECRET_ACCESS_KEY, settings.S3_BUCKET_NAME]) else None