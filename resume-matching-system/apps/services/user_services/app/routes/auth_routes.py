from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
import random
from datetime import datetime, timedelta

from resources.database.session import get_db
from resources.auth.jwt_handler import create_access_token
from ..models.user_model import User
from ..schemas.user_schemas import PhoneSchema, OTPVerifySchema

from apps.services.match_services.app.models.upload_model import Resume, JobDescription
from apps.services.match_services.app.models.match_models import MatchResult

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
        "role": existing.role,
        "access_token": token,
        "token_type": "bearer"
    }
    
@router.get("/dashboard/summary")
async def admin_summary(db: Session = Depends(get_db)):
    total_resumes = db.query(Resume).count()
    total_jobs = db.query(JobDescription).count()
    total_matches = db.query(MatchResult).count()

    return {
        "total_resumes": total_resumes,
        "total_jobs": total_jobs,
        "total_matches": total_matches
    }
    
@router.get("/dashboard/job/{jd_id}/ranking")
async def job_ranking(jd_id: str, db: Session = Depends(get_db)):
    jd = db.query(JobDescription).filter(JobDescription.id == jd_id).first()
    if not jd:
        raise HTTPException(status_code=404, detail="Job not found")

    # Get all match results for this job
    matches = (
        db.query(MatchResult)
        .join(Resume, MatchResult.resume_id == Resume.id)
        .filter(MatchResult.jd_id == jd_id)
        .all()
    )

    # Sort by score desc
    ranked = sorted(matches, key=lambda m: m.score, reverse=True)

    response = []
    for m in ranked:
        # get resume again or use relationship
        resume = db.query(Resume).filter(Resume.id == m.resume_id).first()
        response.append({
            "resume_id": m.resume_id,
            "candidate_name": resume.candidate_name,
            "candidate_email": resume.candidate_email,
            "score": m.score,
            "matched_skills": m.matched,
            "missing_skills": m.missing,
            "summary": m.summary,
            "status": "Shortlist" if m.score >= 70 else "Review"
        })

    return {"job_id": jd_id, "job_title": jd.file_name, "candidates": response}

