from fastapi import APIRouter, File, UploadFile, HTTPException, Form
from typing import List
from ..services.s3_service import s3_service
from ..models import UploadResponse
from ..config import settings

router = APIRouter(prefix="/upload", tags=["upload"])

@router.post("/images", response_model=List[UploadResponse])
async def upload_images(files: List[UploadFile] = File(...)):
    """Upload multiple images to S3"""
    if not s3_service:
        raise HTTPException(status_code=500, detail="S3 service not configured")

    if len(files) > 12:  # eBay limit
        raise HTTPException(status_code=400, detail="Maximum 12 images allowed")

    uploaded_files = []

    for file in files:
        # Validate file type
        if file.content_type not in settings.ALLOWED_IMAGE_TYPES:
            raise HTTPException(
                status_code=400,
                detail=f"File {file.filename} has unsupported type {file.content_type}"
            )

        # Validate file size
        content = await file.read()
        if len(content) > settings.MAX_FILE_SIZE:
            raise HTTPException(
                status_code=400,
                detail=f"File {file.filename} exceeds maximum size limit"
            )

        try:
            upload_result = await s3_service.upload_image(
                file_content=content,
                filename=file.filename,
                content_type=file.content_type,
                optimize=True
            )
            uploaded_files.append(upload_result)
        except ValueError as e:
            raise HTTPException(status_code=400, detail=str(e))

    return uploaded_files