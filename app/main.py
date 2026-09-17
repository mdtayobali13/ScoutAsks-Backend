from app.api.router import api_router
from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
import os
from app.core.database import engine, Base
import app.models.user_model
import app.models.home_model
import app.models.job_model

# Create all tables
Base.metadata.create_all(bind=engine)

app = FastAPI(
    title="Scout Asks Backend",
    description="Scout Asks Backend API"
)

# Ensure the uploads directory exists
os.makedirs("uploads", exist_ok=True)
# Mount the uploads directory to serve files publicly
app.mount("/uploads", StaticFiles(directory="uploads"), name="uploads")

app.include_router(api_router)

@app.get("/")
def read_root():
    return {"status":"ok", "data": {"message": "Scout Asks Backend"}}
