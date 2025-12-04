from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List
from collections import Counter
import os

from resources.database.session import get_db
from resources.auth.dependencies import get_admin_user
from apps.services.user_services.app.models.user_model import User
from apps.services.admin_services.app.schemas.job_schemas import JobCreate, JobResponse
from apps.services.admin_services.app.models.job_models import Job
from apps.services.match_services.app.models.upload_model import Resume
from apps.services.match_services.app.models.match_models import MatchResult

from fastapi import UploadFile, File
from libs.service.resume_parser import parse_resume_to_text, extract_skills
from libs.service.embedding_service import generate_embeddings
from libs.service.match_scoring import calculate_similarity_score, skill_gap_analysis
from apps.services.user_services.app.models.user_model import User
from resources.database.base import Base

router = APIRouter(prefix="/jobs", tags=["Jobs"])
BASE_URL = os.getenv("BASE_URL", "http://localhost:8000")


@router.post("/{job_id}/match-all")
def match_all_resumes_for_job(
    job_id: str,
    db: Session = Depends(get_db),
    admin: User = Depends(get_admin_user)
):
    job = db.query(Job).filter(Job.id == job_id).first()
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")

    resumes = db.query(Resume).all()
    if not resumes:
        raise HTTPException(status_code=404, detail="No resumes available")

    results = []

    for resume in resumes:
        # Convert text to embeddings
        resume_emb = generate_embeddings(resume.text)
        jd_emb = generate_embeddings(job.description)

        # Match scoring
        score = calculate_similarity_score(resume_emb, jd_emb)

        # Skill comparison
        matched, missing = skill_gap_analysis(
            resume.text.split(),
            job.required_skills.split(",")
        )
        
        # -------------- SAVE IN DB --------------- #
        match_record = MatchResult(
            score=score,
            matched=matched,
            missing=missing,
            summary=f"Candidate fits {score:.2f}%",
            resume_id=resume.id,
            jd_id=job.id
        )

        db.add(match_record)
        db.commit()
        db.refresh(match_record)

        results.append({
            "resume_id": resume.id,
            "candidate_name": resume.candidate_name,
            "score": round(score, 2),
            "matched": matched,
            "missing": missing
        })

    # Sort by highest score
    results_sorted = sorted(results, key=lambda x: x["score"], reverse=True)

    return {
        "job_id": job_id,
        "matching_results": results_sorted,
        "total_resumes": len(results)
    }
@router.post("/{job_id}/bulk-upload-resumes")
async def bulk_upload_resumes(
    job_id: int,
    files: list[UploadFile] = File(...),
    db: Session = Depends(get_db),
    admin: User = Depends(get_admin_user)
):
    job = db.query(Job).filter(Job.id == job_id).first()
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")

    jd_skills = [s.strip() for s in job.skills_required.split(",") if s.strip()]
    jd_emb = generate_embeddings(job.description)

    results = []

    for file in files:
        contents = await file.read()
        os.makedirs("temp", exist_ok=True)
        temp_path = os.path.join("temp", file.filename)
        with open(temp_path, "wb") as f:
            f.write(contents)

        resume_text = parse_resume_to_text(temp_path)
        resume_skills = extract_skills(resume_text)

        resume_emb = generate_embeddings(resume_text)
        score = calculate_similarity_score(resume_emb, jd_emb)
        matched, missing = skill_gap_analysis(resume_skills, jd_skills)

        resume = Resume(file_name=file.filename, text=resume_text)
        db.add(resume)
        db.commit()
        db.refresh(resume)

        match = MatchResult(
            score=score,
            matched=matched,
            missing=missing,
            summary=f"Candidate fits {score:.2f}%",
            resume_id=resume.id,
            jd_id=job_id
        )
        db.add(match)
        db.commit()

        results.append({
            "resume_id": resume.id,
            "file_name": file.filename,
            "score": score,
            "matched": matched,
            "missing": missing
        })

    results.sort(key=lambda x: x["score"], reverse=True)

    return {
        "job_id": job_id,
        "processed": len(results),
        "results": results
    }


@router.get("/{job_id}/results")
def get_job_results(
    job_id: str,
    db: Session = Depends(get_db),
    admin = Depends(get_admin_user)
):
    job = db.query(Job).filter(Job.id == job_id).first()
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")

    results = (
        db.query(MatchResult)
        .filter(MatchResult.jd_id == job_id)
        .order_by(MatchResult.score.desc())
        .all()
    )

    if not results:
        return {"message": "No match results found for this job"}

    response_data = []
    for r in results:
        resume = db.query(Resume).filter(Resume.id == r.resume_id).first()

        response_data.append({
            "match_id": r.id,
            "candidate_name": resume.candidate_name,
            "candidate_email": resume.candidate_email,
            "candidate_phone": resume.candidate_phone,
            "experience": resume.years_of_experience,
            "score": round(r.score, 2),
            "matched_skills": r.matched,
            "missing_skills": r.missing,
            "summary": r.summary,
            "pdf_report": f"{BASE_URL}/match/report/{r.id}"
        })

    return {
        "job_id": job.id,
        "job_title": job.title,
        "total_applicants": len(results),
        "ranked_results": response_data
    }
    
    
@router.get("/{job_id}/analytics")
def job_analytics(
    job_id: str,
    db: Session = Depends(get_db),
    admin = Depends(get_admin_user)
):
    job = db.query(Job).filter(Job.id == job_id).first()
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")

    results = db.query(MatchResult)\
                .filter(MatchResult.jd_id == job_id)\
                .order_by(MatchResult.score.desc())\
                .all()

    if not results:
        return {"message": "No applicants yet"}

    # Total Applicants
    total = len(results)

    # Average score
    avg_score = sum(r.score for r in results) / total

    # Top candidates
    top_candidates = results[:3]

    top_data = []
    for r in top_candidates:
        resume = db.query(Resume).filter(Resume.id == r.resume_id).first()
        top_data.append({
            "candidate_name": resume.candidate_name,
            "score": round(r.score, 2),
            "experience": resume.years_of_experience
        })

    # Skill gap aggregation
    missing_skills_list = []
    for r in results:
        missing_skills_list.extend(r.missing)

    skill_gap_count = Counter(missing_skills_list).most_common(5)

    # Best suggestion
    best_fit = top_data[0] if top_data else None

    return {
        "job_id": job.id,
        "job_title": job.title,
        "total_applicants": total,
        "average_score": round(avg_score, 2),
        "best_candidate": best_fit,
        "top_candidates": top_data,
        "top_missing_skills": [
            {"skill": s, "count": c} for s, c in skill_gap_count
        ]
    }

@router.get("/{job_id}/ranked-candidates")
async def ranked_candidates(
    job_id: int,
    min_score: float = 0,
    db: Session = Depends(get_db),
    admin: User = Depends(get_admin_user)
):
    job = db.query(Job).filter(Job.id == job_id).first()
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")

    results = (
        db.query(MatchResult)
        .filter(MatchResult.jd_id == job_id)
        .all()
    )

    if not results:
        return {"message": "No match results found for this job"}

    ranked = []

    for r in results:
        resume = db.query(Resume).filter(Resume.id == r.resume_id).first()

        if not resume:
            continue

        experience_score = min(resume.years_of_experience / job.experience_required, 1) * 100
        final_score = (r.score * 0.7) + (experience_score * 0.3)

        if final_score >= min_score:
            ranked.append({
                "resume_id": resume.id,
                "candidate_name": resume.candidate_name,
                "similarity_score": r.score,
                "experience_score": round(experience_score, 2),
                "final_score": round(final_score, 2),
                "matched": r.matched,
                "missing": r.missing
            })

    ranked.sort(key=lambda x: x["final_score"], reverse=True)

    return {
        "job_id": job_id,
        "recommended_count": len(ranked),
        "recommended": ranked
    }


@router.post("/", response_model=JobResponse)
def create_job(
    data: JobCreate,
    db: Session = Depends(get_db),
    admin: User = Depends(get_admin_user)
):
    job = Job(
        title=data.title,
        required_skills=data.required_skills,
        min_experience=data.min_experience,
        description=data.description
    )
    db.add(job)
    db.commit()
    db.refresh(job)
    return job

@router.get("/", response_model=List[JobResponse])
def list_jobs(
    db: Session = Depends(get_db),
    admin: User = Depends(get_admin_user)
):
    return db.query(Job).all()

@router.get("/{job_id}", response_model=JobResponse)
def get_job(
    job_id: str,
    db: Session = Depends(get_db),
    admin: User = Depends(get_admin_user)
):
    job = db.query(Job).filter(Job.id == job_id).first()
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
    return job

@router.put("/{job_id}", response_model=JobResponse)
def update_job(
    job_id: str,
    data: JobCreate,
    db: Session = Depends(get_db),
    admin: User = Depends(get_admin_user)
):
    job = db.query(Job).filter(Job.id == job_id).first()
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")

    job.title = data.title
    job.required_skills = data.required_skills
    job.min_experience = data.min_experience
    job.description = data.description
    db.commit()
    db.refresh(job)
    return job

@router.delete("/{job_id}")
def delete_job(
    job_id: str,
    db: Session = Depends(get_db),
    admin: User = Depends(get_admin_user)
):
    job = db.query(Job).filter(Job.id == job_id).first()
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")

    db.delete(job)
    db.commit()
    return {"message": "Job deleted successfully"}
