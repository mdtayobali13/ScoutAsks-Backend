import os
import sys

# Ensure the app directory is in the python path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.core.database import SessionLocal, engine
from app.models.user_model import User, RoleEnum, TechnicianProfile, Base as UserBase
from app.models.home_model import Category, Base as HomeBase
from app.core.security import hash_password

def seed_db():
    print("Seeding database...")
    UserBase.metadata.create_all(bind=engine)
    HomeBase.metadata.create_all(bind=engine)
    
    db = SessionLocal()
    
    try:
        # 1. Seed Categories
        categories_data = [
            {"name": "Certified plumbers", "starting_rate": 65, "is_popular": True},
            {"name": "Electricians", "starting_rate": 65, "is_popular": True},
            {"name": "Boiler & heating", "starting_rate": 65, "is_popular": False},
            {"name": "Roof & Masonry", "starting_rate": 65, "is_popular": False}
        ]
        
        for c_data in categories_data:
            existing = db.query(Category).filter_by(name=c_data["name"]).first()
            if not existing:
                category = Category(**c_data)
                db.add(category)
        
        # 2. Seed Artisans
        artisans_data = [
            {
                "email": "alex.mercer@example.com",
                "full_name": "Alex Mercer",
                "rate": 65,
                "rating": 4.8,
                "reviews": 124
            },
            {
                "email": "john.doe@example.com",
                "full_name": "John Doe",
                "rate": 50,
                "rating": 4.2,
                "reviews": 340
            },
            {
                "email": "jane.smith@example.com",
                "full_name": "Jane Smith",
                "rate": 80,
                "rating": 5.0,
                "reviews": 85
            }
        ]
        
        for art in artisans_data:
            user = db.query(User).filter_by(email=art["email"]).first()
            if not user:
                user = User(
                    full_name=art["full_name"],
                    email=art["email"],
                    hashed_password=hash_password("password123"),
                    role=RoleEnum.technician,
                    is_verified=True
                )
                db.add(user)
                db.commit()
                db.refresh(user)
                
                profile = TechnicianProfile(
                    user_id=user.id,
                    hourly_rate=art["rate"],
                    rating=art["rating"],
                    reviews_count=art["reviews"]
                )
                db.add(profile)
                db.commit()
        print("Database seeded successfully!")
        
    except Exception as e:
        db.rollback()
        print(f"Error seeding database: {e}")
    finally:
        db.close()

if __name__ == "__main__":
    seed_db()
