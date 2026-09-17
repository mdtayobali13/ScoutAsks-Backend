from sqlalchemy.orm import Session
from app.repositories.user_repository import UserRepository
from app.core.security import hash_password, verify_password

class AuthService:
    def __init__(self, db: Session):
        self.user_repo = UserRepository(db)

    def authenticate_user(self, email: str, password: str):
        user = self.user_repo.get_user_by_email(email)
        if not user or not verify_password(password, user.hashed_password):
            return None
        return user
