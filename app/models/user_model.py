from sqlalchemy import Column , Integer , String , Boolean , DateTime ,Enum, ForeignKey , UUID, Float
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.core.database import Base
import enum
import uuid

class RoleEnum(str , enum.Enum):
    admin = "admin"
    customer = "customer"
    technician = "technician"


class User(Base):
    __tablename__ = "users"    
    id = Column(Integer, primary_key=True, index=True)
    full_name = Column(String, nullable=True) 
    email = Column(String, unique=True, index=True, nullable=False) 
    hashed_password = Column(String, nullable=False)
    role = Column(Enum(RoleEnum), nullable=True)
    is_verified = Column(Boolean, default=False)
    profile_image_url = Column(String, nullable=True)
    otp_code = Column(String, nullable=True)
    otp_expires_at = Column(DateTime(timezone=True), nullable=True)
    government_id = Column(String, nullable=True)
    business_registration = Column(String, nullable=True)
    certifications = Column(String, nullable=True)
    insurance_documents = Column(String, nullable=True)
    
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    refresh_tokens = relationship("RefreshToken", back_populates="user", cascade="all, delete-orphan")
    technician_profile = relationship("TechnicianProfile", back_populates="user", uselist=False, cascade="all, delete-orphan")


class TechnicianProfile(Base):
    __tablename__ = "technician_profiles"
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), unique=True, nullable=False)
    hourly_rate = Column(Integer, default=0)
    rating = Column(Float, default=0.0)
    reviews_count = Column(Integer, default=0)
    
    user = relationship("User", back_populates="technician_profile")



class RefreshToken(Base):
    __tablename__ = "refresh_token"

    id = Column(Integer , primary_key=True , index=True)
    token = Column(String , unique=True ,index=True, nullable=False)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    created_at = Column(DateTime , nullable=False)
    user = relationship("User" , back_populates="refresh_tokens")
    expires_at = Column(DateTime(timezone=True) , nullable=False)
    revoked = Column(Boolean , default=False)
