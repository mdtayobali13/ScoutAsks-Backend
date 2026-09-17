from datetime import datetime, timedelta
from jose import jwt
import bcrypt
import os
import secrets
from dotenv import load_dotenv
from fastapi import HTTPException
from sqlalchemy.orm import Session
import app.models.user_model as model

load_dotenv()

SECRET_KEY = os.getenv("SECRET_KEY")
ALGORITHM = os.getenv("ALGORITHM", "HS256")
ACCESS_TOKEN_EXPIRE_MINUTES = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", "30"))
REFRESH_TOKEN_EXPIRE_DAYS = int(os.getenv("REFRESH_TOKEN_EXPIRE_DAYS", "7"))

def hash_password(password: str):
    hashed = bcrypt.hashpw(password.encode("utf-8"), bcrypt.gensalt())
    return hashed.decode("utf-8")

def verify_password(password: str, hashed_password: str):
    return bcrypt.checkpw(password.encode("utf-8"), hashed_password.encode("utf-8"))

def create_access_token(data: dict):
    to_encode = data.copy()
    expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt

def create_refresh_token(db: Session, user: model.User):
    rew_token = secrets.token_urlsafe(32)
    to_token = model.RefreshToken(
        token=rew_token,
        user_id=user.id,
        created_at=datetime.utcnow(),
        expires_at=datetime.utcnow() + timedelta(days=REFRESH_TOKEN_EXPIRE_DAYS),
        revoked=False
    )
    db.add(to_token)
    db.commit()
    db.refresh(to_token)
    return to_token

def verify_access_token(db: Session, token: str):
    db_token = db.query(model.RefreshToken).filter(
        model.RefreshToken.token == token
    ).first()
    if db_token is None:
        raise HTTPException(
            status_code=401,
            detail="Invalid token"
        )
    if db_token.expires_at < datetime.utcnow():
        db_token.revoked = True
        db.commit()
        raise HTTPException(
            status_code=401,
            detail="Token has expired"
        )
    if db_token.revoked:
        raise HTTPException(
            status_code=401,
            detail="Token is revoked"
        )
    if db_token.user is None:
        raise HTTPException(
            status_code=401,
            detail="User not found"
        )
    return db_token
 
def revoke_refresh_token(db: Session, token: str):
    db_token = db.query(model.RefreshToken).filter(model.RefreshToken.token == token).first()
    if db_token:
        db_token.revoked = True
        db.commit()
