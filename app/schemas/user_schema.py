from pydantic import BaseModel , EmailStr , field_validator 
from typing import Optional
from app.models.user_model import RoleEnum

#-------SignUp Schemas--------

class SignUpRequest(BaseModel):
    email: EmailStr
    full_name: str
    password: str
    confirm_password: str

    @field_validator("confirm_password")
    @classmethod
    def validate_password(cls, v, info):
        if "password" in info.data and v != info.data["password"]:
            raise ValueError("Passwords do not match")
        return v

#-------Login Schemas--------

class LoginRequest(BaseModel):
    email : EmailStr
    password : str
    remember : Optional[bool] = False

#--------Choose your role schemas--------
class choose_role_request(BaseModel):
    role : RoleEnum

#--------OTP Schemas--------

class OTPSentRequest(BaseModel):
    email : EmailStr

class OTPVerifyRequest(BaseModel):
    email : EmailStr
    otp : str

class OTPResendRequest(BaseModel):
    email : EmailStr

#--------User / Token Schemas--------

class UserResponse(BaseModel):
    id : int
    email : EmailStr
    full_name : Optional[str] = None
    role : Optional[RoleEnum] = None
    is_verified : Optional[bool] = False
    profile_image_url : Optional[str] = None
    
    class Config:
        from_attributes = True

# Keep LogoutRequest alias for compatibility
LogoutRequest = UserResponse

#--------Token Schemas--------
class TokenResponse(BaseModel):
    access_token : str
    refresh_token : str
    token_type : str = "Bearer"
    user : UserResponse

class MessageResponse(BaseModel):
    message : str
    
#--------refresh token Schemas--------

class RefreshTokenRequest(BaseModel):
    refresh_token : str

class RefreshTokenResponse(BaseModel):
    message : Optional[str] = "Token refreshed successfully"
    access_token : str
    refresh_token : str
    token_type : str = "Bearer"

#--------Password Recovery Schemas--------

class ForgotPasswordRequest(BaseModel):
    email : EmailStr

class VerifyResetOTPRequest(BaseModel):
    otp : str

VerifyResetCodeRequest = VerifyResetOTPRequest

class VerifyResetOTPResponse(BaseModel):
    message : str
    email : Optional[str] = None
    reset_token : Optional[str] = None

VerifyResetCodeResponse = VerifyResetOTPResponse

class ResetPasswordRequest(BaseModel):
    password : str
    confirm_password : str

    @field_validator("confirm_password")
    @classmethod
    def validate_passwords_match(cls, v, info):
        if "password" in info.data and v != info.data["password"]:
            raise ValueError("Passwords do not match")
        return v
