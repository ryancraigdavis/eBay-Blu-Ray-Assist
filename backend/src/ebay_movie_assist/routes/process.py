from fastapi import APIRouter, HTTPException
from typing import List
from ..models import BlurayItem, ProcessingRequest, ProcessingResponse, MovieMetadata, PriceData
from ..services.tmdb_service import tmdb_service
from ..services.pricing_service import pricing_service
from ..services.template_service import template_service

router = APIRouter(prefix="/process", tags=["process"])

@router.get("/metadata", response_model=MovieMetadata)
async def get_movie_metadata(title: str, year: int = None):
    """Get movie metadata from TMDB"""
    # If TMDB service not configured, return mock data
    if not tmdb_service:
        return MovieMetadata(
            title=title,
            original_title=title,
            release_date=f"{year or 2020}-01-01",
            genres=["Action", "Thriller"],
            director="Unknown Director",
            actors=["Actor 1", "Actor 2", "Actor 3"],
            studio="Universal Pictures",
            rating="PG-13",
            runtime=120,
            overview=f"This is a mock overview for {title}. TMDB credentials are not configured.",
            poster_url=None
        )

    try:
        metadata = await tmdb_service.search_movie(title, year)
        if not metadata:
            raise HTTPException(status_code=404, detail="Movie not found")
        return metadata
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/pricing", response_model=PriceData)
async def get_pricing_data(title: str, condition: str = "Used"):
    """Get pricing data for a movie title"""
    try:
        pricing_data = await pricing_service.get_comprehensive_pricing(title, condition)
        if not pricing_data:
            raise HTTPException(status_code=404, detail="Pricing data not found")
        return pricing_data
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/items", response_model=ProcessingResponse)
async def process_bluray_items(request: ProcessingRequest):
    """Process multiple blu-ray items to get metadata, pricing, and template data"""
    processed_items = []
    template_data = []
    errors = []

    for item in request.items:
        try:
            # Get metadata if not already present
            if not item.metadata and item.title:
                if tmdb_service:
                    metadata = await tmdb_service.search_movie(item.title)
                    if metadata:
                        item.metadata = metadata

            # Get pricing data if not already present
            if not item.price_data and item.title:
                pricing_data = await pricing_service.get_comprehensive_pricing(
                    item.title, item.condition
                )
                if pricing_data:
                    item.price_data = pricing_data

            # Create template row
            template_row = template_service.create_listing_row(item)
            template_data.append(template_row)

            processed_items.append(item)

        except Exception as e:
            errors.append(f"Error processing item '{item.title}': {str(e)}")
            # Still add the item even if processing failed
            processed_items.append(item)
            template_data.append(template_service.create_listing_row(item))

    return ProcessingResponse(
        success=len(errors) == 0,
        items=processed_items,
        template_data=template_data,
        errors=errors
    )

@router.post("/single-item", response_model=BlurayItem)
async def process_single_item(
    title: str,
    condition: str = "Used",
    photos: List[str] = None,
    user_notes: str = None
):
    """Process a single blu-ray item"""
    item = BlurayItem(
        title=title,
        condition=condition,
        photos=photos or [],
        user_notes=user_notes
    )

    # Get metadata
    if tmdb_service:
        metadata = await tmdb_service.search_movie(title)
        if metadata:
            item.metadata = metadata

    # Get pricing data
    pricing_data = await pricing_service.get_comprehensive_pricing(title, condition)
    if pricing_data:
        item.price_data = pricing_data

    return item