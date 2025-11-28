from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
import random
from datetime import datetime, timedelta

from resources.database.session import get_db
from resources.auth.jwt_handler import create_access_token
from ..models.user_model import User
from ..schemas.user_schemas import PhoneSchema, OTPVerifySchema

router = APIRouter(prefix="/auth", tags=["Auth"])

# Temporary in-memory OTP storage (you can replace using Redis later)
otp_store = {}

@router.post("/register")
def register(data: PhoneSchema, db: Session = Depends(get_db)):
    phone = data.phone

    otp = random.randint(100000, 999999)
    otp_store[phone] = {"otp": otp, "expires": datetime.utcnow() + timedelta(minutes=5)}

    print("OTP:", otp)  # TODO: integrate SMS gateway

    return {"message": "OTP sent successfully",
            "otp": otp}

@router.post("/verify")
def verify(data: OTPVerifySchema, db: Session = Depends(get_db)):
    stored = otp_store.get(data.phone)

    if not stored or stored["otp"] != data.otp:
        raise HTTPException(status_code=400, detail="Invalid OTP")

    if stored["expires"] < datetime.utcnow():
        raise HTTPException(status_code=400, detail="OTP expired")

    # Check if user exists
    existing = db.query(User).filter(User.phone == data.phone).first()

    if not existing:
        new_user = User(phone=data.phone)
        db.add(new_user)
        db.commit()
        db.refresh(new_user)
        existing = new_user

    token = create_access_token({"sub": existing.phone})

    del otp_store[data.phone]  # Clear used OTP

    return {
        "message": "Verification successful",
        "user": {"id": existing.id, "phone": existing.phone},
        "access_token": token,
        "token_type": "bearer"
    }
