from fastapi import APIRouter, UploadFile, File, Depends, HTTPException
from sqlalchemy.orm import Session
import os

from resources.database.session import get_db
from apps.services.match_services.app.models.upload_model import Resume, JobDescription
from apps.services.match_services.app.dto.upload_dto import ResumeUpdateDto, JDUpdateDto
from libs.service.resume_parser import parse_resume_to_text
from libs.service.jd_parser import parse_job_description

router = APIRouter(prefix="/upload", tags=["Upload CRUD"])

# ---------------------- RESUME CRUD -----------------------

@router.get("/resume/{resume_id}")
async def get_resume(resume_id: str, db: Session = Depends(get_db)):
    result = db.query(Resume).filter(Resume.id == resume_id).first()
    if not result:
        raise HTTPException(status_code=404, detail="Resume not found")
    return result

@router.put("/resume/{resume_id}")
async def update_resume(resume_id: str, data: ResumeUpdateDto, db: Session = Depends(get_db)):
    result = db.query(Resume).filter(Resume.id == resume_id).first()
    if not result:
        raise HTTPException(status_code=404, detail="Resume not found")

    for field, value in data.dict(exclude_unset=True).items():
        setattr(result, field, value)

    db.commit()
    return {"message": "Resume updated"}

@router.delete("/resume/{resume_id}")
async def delete_resume(resume_id: str, db: Session = Depends(get_db)):
    result = db.query(Resume).filter(Resume.id == resume_id).first()
    if not result:
        raise HTTPException(status_code=404, detail="Resume not found")

    db.delete(result)
    db.commit()
    return {"message": "Resume deleted"}

# ---------------------- JOB DESCRIPTION CRUD -----------------------

@router.get("/jd/{jd_id}")
async def get_jd(jd_id: str, db: Session = Depends(get_db)):
    result = db.query(JobDescription).filter(JobDescription.id == jd_id).first()
    if not result:
        raise HTTPException(status_code=404, detail="JD not found")
    return result

@router.put("/jd/{jd_id}")
async def update_jd(jd_id: str, data: JDUpdateDto, db: Session = Depends(get_db)):
    result = db.query(JobDescription).filter(JobDescription.id == jd_id).first()
    if not result:
        raise HTTPException(status_code=404, detail="JD not found")

    for field, value in data.dict(exclude_unset=True).items():
        setattr(result, field, value)

    db.commit()
    return {"message": "JD updated"}

@router.delete("/jd/{jd_id}")
async def delete_jd(jd_id: str, db: Session = Depends(get_db)):
    result = db.query(JobDescription).filter(JobDescription.id == jd_id).first()
    if not result:
        raise HTTPException(status_code=404, detail="JD not found")

    db.delete(result)
    db.commit()
    return {"message": "JD deleted"}
