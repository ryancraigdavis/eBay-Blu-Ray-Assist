from fastapi import APIRouter, HTTPException
from fastapi.responses import FileResponse
from typing import List
import tempfile
import os
from ..models import BlurayItem
from ..services.template_service import template_service

router = APIRouter(prefix="/template", tags=["template"])

@router.post("/generate-csv")
async def generate_ebay_csv(items: List[BlurayItem]):
    """Generate eBay CSV template from processed items"""
    if not items:
        raise HTTPException(status_code=400, detail="No items provided")

    try:
        # Create temporary file
        with tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False) as temp_file:
            output_path = temp_file.name

        # Generate CSV
        csv_path = template_service.export_to_csv(items, output_path)

        # Return file response
        return FileResponse(
            path=csv_path,
            filename=f"ebay_bluray_listings_{len(items)}_items.csv",
            media_type="text/csv",
            background=lambda: os.unlink(csv_path)  # Delete temp file after sending
        )

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to generate CSV: {str(e)}")

@router.post("/preview")
async def preview_template_data(items: List[BlurayItem]):
    """Preview template data without generating file"""
    if not items:
        raise HTTPException(status_code=400, detail="No items provided")

    try:
        template_data = template_service.create_template_data(items)
        return {
            "item_count": len(items),
            "template_data": template_data
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to create template data: {str(e)}")