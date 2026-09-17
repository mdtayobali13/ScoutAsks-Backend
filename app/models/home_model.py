from sqlalchemy import Column, Integer, String, Boolean
from app.core.database import Base

class Category(Base):
    __tablename__ = "categories"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, unique=True, index=True, nullable=False)
    image_url = Column(String, nullable=True)
    starting_rate = Column(Integer, default=0) # e.g., 65 for €65/hr
    is_popular = Column(Boolean, default=False)
