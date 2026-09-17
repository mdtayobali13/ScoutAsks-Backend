import os
import shutil
from typing import Optional, List
from datetime import datetime, timezone, timedelta

from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, File, Form, Request
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session

import app.schemas.user_schema as schemas
import app.models.user_model as model
from app.core.database import get_db
from app.core.security import (
    hash_password, verify_password, create_access_token,
    create_refresh_token, verify_access_token, revoke_refresh_token,
    SECRET_KEY, ALGORITHM
)
from app.core.dependencies import get_current_user
from app.utils.helpers import generate_otp, get_otp_expiry
from app.utils.email import send_otp_mail

router = APIRouter(
    prefix="/auth",
    tags=["Authentication"]
)


@router.post("/signup/customer", response_model= schemas.MessageResponse )
def signup_user(payload : schemas.SignUpRequest , db:Session= Depends(get_db)):
          
    existing_user = db.query(model.User).filter(model.User.email == payload.email).first()

    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="User with this email already exists"
        )
    new_user = model.User(
        email = payload.email,
        full_name = payload.full_name,
        hashed_password = hash_password(payload.password),
        role = model.RoleEnum.customer,
        is_verified = False
    )

    otp_code =  generate_otp() 
    new_user.otp_code = otp_code
    new_user.otp_expires_at = get_otp_expiry()
    
    db.add(new_user)
    db.commit()
    db.refresh(new_user)
    send_otp_mail(new_user.email , otp_code)

    return {
        "message" :"Customer created successfully. Please check your email for the OTP."
    }


@router.post("/signup/admin", response_model= schemas.MessageResponse )
def signup_admin(payload : schemas.SignUpRequest , db:Session= Depends(get_db)):
          
    existing_user = db.query(model.User).filter(model.User.email == payload.email).first()

    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="User with this email already exists"
        )
    new_user = model.User(
        email = payload.email,
        full_name = payload.full_name,
        hashed_password = hash_password(payload.password),
        role = model.RoleEnum.admin,
        is_verified = False
    )

    otp_code =  generate_otp() 
    new_user.otp_code = otp_code
    new_user.otp_expires_at = get_otp_expiry()
    
    db.add(new_user)
    db.commit()
    db.refresh(new_user)
    send_otp_mail(new_user.email , otp_code)

    return {
        "message" :"Admin created successfully. Please check your email for the OTP."
    }

BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
UPLOAD_DIR = os.path.join(BASE_DIR, "uploads", "technicians")
os.makedirs(UPLOAD_DIR, exist_ok=True)

@router.post("/signup/technician", response_model= schemas.MessageResponse)
async def signup_technician(
    email: str = Form(...),
    full_name: str = Form(...),
    password: str = Form(...),
    confirm_password: str = Form(...),
    government_id: UploadFile = File(...),
    certifications: UploadFile = File(...),
    insurance_documents: UploadFile = File(...),
    business_registration: Optional[UploadFile] = File(None),
    db: Session = Depends(get_db)
):
    if password != confirm_password:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Passwords do not match"
        )
        
    existing_user = db.query(model.User).filter(model.User.email == email).first()
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="User with this email already exists"
        )
        
    def save_file(file: UploadFile, prefix: str):
        if not file:
            return None
        file_extension = os.path.splitext(file.filename)[1]
        file_name = f"{prefix}_{email}{file_extension}"
        file_path = os.path.join(UPLOAD_DIR, file_name)
        with open(file_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)
        return file_path

    gov_id_path = save_file(government_id, "govid")
    cert_path = save_file(certifications, "cert")
    ins_path = save_file(insurance_documents, "ins")
    biz_path = save_file(business_registration, "biz") if business_registration else None

    new_user = model.User(
        email=email,
        full_name=full_name,
        hashed_password=hash_password(password),
        role=model.RoleEnum.technician,
        is_verified=False,
        government_id=gov_id_path,
        certifications=cert_path,
        insurance_documents=ins_path,
        business_registration=biz_path
    )

    otp_code = generate_otp()
    new_user.otp_code = otp_code
    new_user.otp_expires_at = get_otp_expiry()
    
    db.add(new_user)
    db.commit()
    db.refresh(new_user)
    send_otp_mail(new_user.email, otp_code)

    return {
        "message": "Technician created successfully. Please check your email for the OTP."
    }



@router.post("/signup/verify-otp", response_model=schemas.MessageResponse, summary="Verify Signup OTP")
def verify_otp(payload : schemas.OTPVerifyRequest , db:Session= Depends(get_db)):
     user = db.query(model.User).filter(model.User.email == payload.email).first()
     if not user: 
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="User not found"
        )

     if not payload.otp or str(user.otp_code) != str(payload.otp):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid OTP"
        )

     if user.otp_expires_at:
        now = datetime.now(timezone.utc)
        expires_at = user.otp_expires_at
        if expires_at.tzinfo is None:
            expires_at = expires_at.replace(tzinfo=timezone.utc)
        if expires_at < now:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="OTP has expired"
            )
    
     user.is_verified = True
     user.otp_code = None
     user.otp_expires_at = None
     db.commit()
     db.refresh(user)
     return {
        "message": "User verified successfully"
    }

@router.post("/signup/resend-otp", response_model=schemas.MessageResponse, summary="Resend Signup OTP")
def resend_otp(payload : schemas.OTPResendRequest , db:Session= Depends(get_db)):
    user = db.query(model.User).filter(model.User.email == payload.email).first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="User not found"
        )
    otp_code = generate_otp()
    user.otp_code = otp_code
    user.otp_expires_at = get_otp_expiry()
    db.commit()
    db.refresh(user)
    send_otp_mail(user.email , otp_code)
    return {
        "message": "OTP resent successfully"
    }


@router.post("/login", response_model=schemas.TokenResponse)
def login_user(payload: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_db)):
    user = db.query(model.User).filter(model.User.email == payload.username).first()
    
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Account not found. Please check your email or sign up."
        )
        
    if not verify_password(payload.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect password. Please try again."
        )
    if not user.is_verified:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="User is not verified"
        )
    
    access_token = create_access_token(data={"sub": user.email})
    refresh_token = create_refresh_token(db, user)
    return {
        "access_token": access_token,
        "refresh_token": refresh_token.token,
        "token_type": "Bearer",
        "user": user
    }

@router.post("/choose-role", response_model=schemas.MessageResponse)
def choose_role(payload : schemas.choose_role_request , current_user : model.User = Depends(get_current_user) , db:Session= Depends(get_db)):
    current_user.role = payload.role
    db.commit()
    db.refresh(current_user)
    return {
        "message": "User role updated successfully"
    }

@router.post("/refresh-token", response_model=schemas.RefreshTokenResponse)
def refresh_token(payload : schemas.RefreshTokenRequest , db:Session= Depends(get_db)):
    old_token_record = verify_access_token(db , payload.refresh_token)
    user = old_token_record.user
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    
    revoke_refresh_token(db , payload.refresh_token)
    new_access_token = create_access_token(data={"sub": user.email})
    new_refresh_token = create_refresh_token(db, user)
    return {
        "message": "Token refreshed successfully" ,
        "access_token": new_access_token,
        "refresh_token": new_refresh_token.token,
        "token_type": "Bearer"
    }


@router.post("/logout", response_model=schemas.MessageResponse)
def logout_user(payload : schemas.RefreshTokenRequest , db:Session= Depends(get_db)):
    old_token_record = verify_access_token(db , payload.refresh_token)
    revoke_refresh_token(db , payload.refresh_token)
    return {
        "message": "User logout successfully"
    }


@router.post("/password/forgot", response_model=schemas.MessageResponse, summary="Restore Your Shield (Send Code)")
def forgot_password(payload: schemas.ForgotPasswordRequest, db: Session = Depends(get_db)):
    user = db.query(model.User).filter(model.User.email == payload.email).first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User with this email not found"
        )
    
    code = generate_otp()
    user.otp_code = code
    user.otp_expires_at = get_otp_expiry()
    db.commit()
    db.refresh(user)

    send_otp_mail(user.email, code)

    return {
        "message": "Recovery code sent to your email successfully"
    }

@router.post("/password/verify-otp", response_model=schemas.VerifyResetOTPResponse, summary="Verify Password Reset OTP")
def verify_reset_otp(payload: schemas.VerifyResetOTPRequest, db: Session = Depends(get_db)):
    otp_str = payload.otp.strip()
    user = db.query(model.User).filter(model.User.otp_code == otp_str).first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid OTP"
        )
    
    if user.otp_expires_at:
        now = datetime.now(timezone.utc)
        expires_at = user.otp_expires_at
        if expires_at.tzinfo is None:
            expires_at = expires_at.replace(tzinfo=timezone.utc)
        if expires_at < now:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="OTP has expired"
            )

    user.otp_code = "RESET_VERIFIED"
    user.otp_expires_at = datetime.now(timezone.utc) + timedelta(minutes=15)
    db.commit()
    db.refresh(user)


    reset_token = create_access_token(data={"sub": user.email, "type": "password_reset"})

    return {
        "message": "OTP verified successfully",
        "email": user.email,
        "reset_token": reset_token
    }

@router.post("/password/reset", response_model=schemas.MessageResponse, summary="Create New Password (Update Password)")
def reset_password(
    payload: schemas.ResetPasswordRequest,
    request: Request,
    db: Session = Depends(get_db)
):
    user = None

    auth_header = request.headers.get("Authorization")
    if auth_header and auth_header.startswith("Bearer "):
        token = auth_header.split(" ")[1]
        try:
            from jose import jwt, JWTError
            token_payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
            user_email = token_payload.get("sub")
            if user_email and token_payload.get("type") == "password_reset":
                user = db.query(model.User).filter(model.User.email == user_email).first()
        except Exception:
            pass

    if not user and request.query_params.get("token"):
        try:
            from jose import jwt, JWTError
            token_payload = jwt.decode(request.query_params.get("token"), SECRET_KEY, algorithms=[ALGORITHM])
            user_email = token_payload.get("sub")
            if user_email and token_payload.get("type") == "password_reset":
                user = db.query(model.User).filter(model.User.email == user_email).first()
        except Exception:
            pass

  
    if not user:
        now = datetime.now(timezone.utc)
        user = db.query(model.User).filter(
            model.User.otp_code == "RESET_VERIFIED",
            model.User.otp_expires_at >= now
        ).order_by(model.User.otp_expires_at.desc()).first()

    if not user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No verified reset request found or session expired. Please verify code again."
        )

  
    user.hashed_password = hash_password(payload.password)
    user.otp_code = None
    user.otp_expires_at = None
    db.commit()
    db.refresh(user)

    return {
        "message": "Password updated successfully"
    }


@router.get("/me", response_model=schemas.UserResponse, summary="Get Current Logged in User")
def get_user_me(current_user: model.User = Depends(get_current_user)):
    return current_user

@router.get("/users", response_model=List[schemas.UserResponse], summary="Get All Users")
def get_all_users(db: Session = Depends(get_db)):
    users = db.query(model.User).all()
    return users

@router.delete("/delete-account", response_model=schemas.MessageResponse, summary="Delete Current User Account")
def delete_account(
    payload: schemas.LoginRequest,
    current_user: model.User = Depends(get_current_user), 
    db: Session = Depends(get_db)
):
    if current_user.email != payload.email or not verify_password(payload.password, current_user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid email or password"
        )
        
    db.delete(current_user)
    db.commit()
    return {"message": "Account deleted successfully"}

