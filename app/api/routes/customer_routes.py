from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from typing import List, Optional

from app.core.database import get_db
from app.core.dependencies import get_current_user, get_current_customer
import app.models.user_model as user_model
import app.models.home_model as home_model
import app.models.job_model as job_model
import app.schemas.home_schema as schemas
import app.schemas.job_schema as job_schemas

router = APIRouter(
    prefix="/customer",
    tags=["Customer Home Screen"],
    dependencies=[Depends(get_current_customer)]
)

@router.get("/categories", response_model=List[schemas.CategoryResponse], summary="Get All Categories")
def get_categories(
    tab: Optional[str] = "all", 
    search: Optional[str] = None,
    db: Session = Depends(get_db)
):
    query = db.query(home_model.Category)
    
    if tab and tab.lower() == "popular":
        query = query.filter(home_model.Category.is_popular == True)
        
    if search:
        query = query.filter(home_model.Category.name.ilike(f"%{search}%"))
        
    categories = query.all()
    return categories

@router.get("/artisans", response_model=List[schemas.ArtisanResponse], summary="Get Artisans / Technicians")
def get_artisans(
    tab: Optional[str] = "recommend", 
    db: Session = Depends(get_db)
):
    # We join with TechnicianProfile so that only technicians WITH a profile are returned
    query = db.query(user_model.User).join(user_model.TechnicianProfile).filter(
        user_model.User.role == user_model.RoleEnum.technician
    )
    
    if tab:
        tab_lower = tab.lower()
        if tab_lower == "top_rated":
            # Order by rating descending
            query = query.order_by(user_model.TechnicianProfile.rating.desc())
        elif tab_lower == "popular":
            # Order by number of reviews descending
            query = query.order_by(user_model.TechnicianProfile.reviews_count.desc())
        elif tab_lower == "near":
            # Since we don't have location yet, we'll order by ID descending to show different data
            query = query.order_by(user_model.User.id.desc())
        elif tab_lower == "recommend":
            # Recommend based on a combination of rating and reviews, or just random/default
            # For now, order by ID ascending
            query = query.order_by(user_model.User.id.asc())
    
    artisans = query.all()
    return artisans

@router.get("/recent-viewed", response_model=List[schemas.ArtisanResponse], summary="Get Recently Viewed Artisans")
def get_recent_viewed(
    current_user: user_model.User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    recent_artisans = db.query(user_model.User).join(user_model.TechnicianProfile).filter(
        user_model.User.role == user_model.RoleEnum.technician
    ).limit(3).all()
    return recent_artisans

@router.get("/sos/services", response_model=List[str], summary="Get SOS Services Dropdown")
def get_sos_services():
    return ["Water leak", "Fire", "Medical emergency", "Gas leak"]

@router.get("/sos/priorities", response_model=List[str], summary="Get SOS Priorities Dropdown")
def get_sos_priorities():
    return ["High urgency", "Medium urgency", "Low urgency"]

@router.post("/sos-broadcast", response_model=job_schemas.SosBroadcastWithArtisansResponse, summary="Broadcast SOS Emergency")
def broadcast_sos(
    payload: job_schemas.SosBroadcastCreate,
    current_user: user_model.User = Depends(get_current_customer),
    db: Session = Depends(get_db)
):
    broadcast = job_model.SosBroadcast(
        customer_id=current_user.id,
        service_name=payload.service_name,
        dispatch_priority=payload.dispatch_priority,
        latitude=payload.latitude,
        longitude=payload.longitude,
        status="pending"
    )
    db.add(broadcast)
    db.commit()
    db.refresh(broadcast)
    
    # Find matching technicians (for now, just returning all verified technicians with a profile)
    matched_artisans = db.query(user_model.User).join(user_model.TechnicianProfile).filter(
        user_model.User.role == user_model.RoleEnum.technician
    ).all()
    
    return {
        "broadcast": broadcast,
        "matched_artisans": matched_artisans
    }
