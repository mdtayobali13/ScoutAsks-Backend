from pydantic import BaseModel
from typing import Optional, List
from app.schemas.home_schema import ArtisanResponse

class SosBroadcastCreate(BaseModel):
    service_name: str
    dispatch_priority: str
    latitude: Optional[float] = None
    longitude: Optional[float] = None

class SosBroadcastResponse(SosBroadcastCreate):
    id: int
    customer_id: int
    status: str
    
    class Config:
        from_attributes = True

class SosBroadcastWithArtisansResponse(BaseModel):
    broadcast: SosBroadcastResponse
    matched_artisans: List[ArtisanResponse]
