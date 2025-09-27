from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any
from datetime import datetime

class MovieMetadata(BaseModel):
    title: str
    original_title: Optional[str] = None
    release_date: Optional[str] = None
    genres: List[str] = []
    director: Optional[str] = None
    actors: List[str] = []
    studio: Optional[str] = None
    rating: Optional[str] = None
    runtime: Optional[int] = None
    overview: Optional[str] = None
    poster_url: Optional[str] = None

class PriceData(BaseModel):
    average_price: Optional[float] = None
    shipping_cost: Optional[float] = None
    total_cost: Optional[float] = None
    comparable_listings: List[Dict[str, Any]] = []

class BlurayItem(BaseModel):
    title: str
    condition: str = "Used"
    photos: List[str] = []  # S3 URLs
    metadata: Optional[MovieMetadata] = None
    price_data: Optional[PriceData] = None
    user_notes: Optional[str] = None
    custom_fields: Dict[str, Any] = {}

class ProcessingRequest(BaseModel):
    items: List[BlurayItem]

class ProcessingResponse(BaseModel):
    success: bool
    items: List[BlurayItem]
    template_data: List[Dict[str, Any]]
    errors: List[str] = []

class UploadResponse(BaseModel):
    filename: str
    s3_url: str
    size: int
    content_type: str