from pydantic import BaseModel
from typing import Optional, List

class CategoryResponse(BaseModel):
    id: int
    name: str
    image_url: Optional[str] = None
    starting_rate: int
    is_popular: bool = False

    class Config:
        from_attributes = True

class TechnicianProfileResponse(BaseModel):
    hourly_rate: int
    rating: float
    reviews_count: int

    class Config:
        from_attributes = True

class ArtisanResponse(BaseModel):
    id: int
    full_name: Optional[str]
    email: str
    is_verified: bool
    profile_image_url: Optional[str] = None
    technician_profile: Optional[TechnicianProfileResponse] = None

    class Config:
        from_attributes = True
