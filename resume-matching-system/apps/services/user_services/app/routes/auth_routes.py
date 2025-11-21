from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from resources.database.session import get_db
from resources.auth.password_hash import hash_password, verify_password
from resources.auth.jwt_handler import create_access_token
from ..models.user_model import User
from ..schemas.user_schemas import UserCreate, UserLogin, UserResponse

router = APIRouter(prefix="/auth", tags=["Auth"])

@router.post("/register", response_model=UserResponse)
def register(user: UserCreate, db: Session = Depends(get_db)):
    existing = db.query(User).filter(User.email == user.email).first()
    if existing:
        raise HTTPException(status_code=400, detail="Email already registered")

    hashed = hash_password(user.password)
    new_user = User(name=user.name, email=user.email, password=hashed)
    db.add(new_user)
    db.commit()
    db.refresh(new_user)
    return new_user

@router.post("/login")
def login(user: UserLogin, db: Session = Depends(get_db)):
    existing = db.query(User).filter(User.email == user.email).first()
    if not existing or not verify_password(user.password, existing.password):
        raise HTTPException(status_code=401, detail="Invalid credentials")

    token = create_access_token({"sub": existing.email})
    return {
            "user": {"id": existing.id, "name": existing.name, "email": existing.email, "role": existing.role,"access_token": token, "token_type": "bearer"}
            }
