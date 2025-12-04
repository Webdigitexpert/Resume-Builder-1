
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from datetime import datetime
from uuid import uuid4

from resources.database.session import get_db
from resources.auth.dependencies import get_current_user

from apps.services.match_services.app.models.upload_model import Resume
from apps.services.admin_services.app.models.job_models import Job   # <-- Verify path
from apps.services.match_services.app.models.upload_model import JobApplication
from apps.services.match_services.app.models.upload_model import Resume, JobDescription
from apps.services.match_services.app.models.match_models import MatchResult

# ML / NLP services
from libs.service.embedding_service import generate_embeddings
from libs.service.match_scoring import calculate_similarity_score, skill_gap_analysis



from fastapi import APIRouter
router = APIRouter()

@router.post("/jobs/{job_id}/apply")
async def apply_to_job(
    job_id: str,
    resume_id: str,  # or file upload if you want to upload + apply in one shot
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
):
    # check job exists and is open
    job = db.query(Job).filter(Job.id == job_id).first()
    if not job:
        raise HTTPException(404, "Job not found")

    resume = db.query(Resume).filter(Resume.id == resume_id).first()
    if not resume:
        raise HTTPException(404, "Resume not found")

    application = JobApplication(
        job_id=job.id,
        resume_id=resume.id,
        user_id=current_user.id
    )
    db.add(application)
    db.commit()
    db.refresh(application)

    return {"message": "Applied successfully", "application_id": application.id}

@router.post("/job/{job_id}")
async def match_all_for_job(
    job_id: str,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)  # maybe ensure recruiter/admin
):
    # 1. Get job & JD
    job = db.query(Job).filter(Job.id == job_id).first()
    if not job:
        raise HTTPException(404, "Job not found")

    jd = db.query(JobDescription).filter(JobDescription.id == job.jd_id).first()
    if not jd:
        raise HTTPException(404, "JD not found for this job")

    # 2. Get all applications for this job
    applications = db.query(JobApplication).filter(JobApplication.job_id == job_id).all()
    if not applications:
        return {"job_id": job_id, "candidates": []}

    jd_emb = generate_embeddings(jd.text)

    candidates = []

    for app in applications:
        resume = db.query(Resume).filter(Resume.id == app.resume_id).first()
        if not resume:
            continue

        resume_emb = generate_embeddings(resume.text)
        score = calculate_similarity_score(resume_emb, jd_emb)
        matched, missing = skill_gap_analysis(resume.text.split(), jd.text.split())

        result = MatchResult(
            score=score,
            matched=matched,
            missing=missing,
            summary=f"Candidate fits {score:.2f}%",
            resume_id=resume.id,
            jd_id=jd.id
        )
        db.add(result)

        candidates.append({
            "application_id": app.id,
            "resume_id": resume.id,
            "score": score,
            "matched_skills": matched,
            "missing_skills": missing
        })

    db.commit()

    # sort by score desc
    candidates.sort(key=lambda c: c["score"], reverse=True)

    return {
        "job_id": job_id,
        "total_applicants": len(candidates),
        "candidates": candidates
    }
