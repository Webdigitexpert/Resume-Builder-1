# from fastapi import APIRouter, Depends, HTTPException
# from sqlalchemy.orm import Session
# from typing import List
# import os

# from resources.database.session import get_db
# from resources.auth.dependencies import get_admin_user
# from apps.services.user_services.app.models.user_model import User
# from apps.services.admin_services.app.schemas.job_schemas import JobCreate, JobResponse
# from apps.services.admin_services.app.models.job_models import Job


# from fastapi import UploadFile, File
# from libs.service.resume_parser import parse_resume_to_text, extract_skills
# from libs.service.embedding_service import generate_embeddings
# from libs.service.match_scoring import calculate_similarity_score, skill_gap_analysis
# from apps.services.user_services.app.models.user_model import User

# router = APIRouter(prefix="/jobs", tags=["Jobs"])




# @router.post("/{job_id}/match-resume")
# async def match_resume_to_job(
#     job_id: int,
#     file: UploadFile = File(...),
#     db: Session = Depends(get_db),
#     admin: User = Depends(get_admin_user)
# ):
#     job = db.query(Job).filter(Job.id == job_id).first()
#     if not job:
#         raise HTTPException(status_code=404, detail="Job not found")

#     contents = await file.read()
#     os.makedirs("temp", exist_ok=True)
#     temp_path = os.path.join("temp", file.filename)
#     with open(temp_path, "wb") as f:
#         f.write(contents)

#     resume_text = parse_resume_to_text(temp_path)
#     resume_skills = extract_skills(resume_text)

#     jd_skills = [s.strip() for s in job.skills_required.split(",") if s.strip()]
#     resume_emb = generate_embeddings(resume_text)
#     jd_emb = generate_embeddings(job.description)

#     score = calculate_similarity_score(resume_emb, jd_emb)
#     matched, missing = skill_gap_analysis(resume_skills, jd_skills)

#     return {
#         "job_id": job_id,
#         "score": score,
#         "resume_skills": resume_skills,
#         "jd_skills": jd_skills,
#         "matched": matched,
#         "missing": missing,
#     }





# @router.post("/", response_model=JobResponse)
# def create_job(
#     job: JobCreate,
#     db: Session = Depends(get_db),
#     admin: User = Depends(get_admin_user)
# ):
#     skills_str = ",".join(job.skills_required)
#     new_job = Job(
#         title=job.title,
#         description=job.description,
#         skills_required=skills_str,
#         experience_required=job.experience_required,
#     )
#     db.add(new_job)
#     db.commit()
#     db.refresh(new_job)
#     return new_job

# @router.get("/", response_model=List[JobResponse])
# def list_jobs(
#     db: Session = Depends(get_db),
#     admin: User = Depends(get_admin_user)
# ):
#     return db.query(Job).all()

# @router.get("/{job_id}", response_model=JobResponse)
# def get_job(
#     job_id: int,
#     db: Session = Depends(get_db),
#     admin: User = Depends(get_admin_user)
# ):
#     job = db.query(Job).filter(Job.id == job_id).first()
#     if not job:
#         raise HTTPException(status_code=404, detail="Job not found")
#     return job

# @router.put("/{job_id}", response_model=JobResponse)
# def update_job(
#     job_id: int,
#     job_data: JobCreate,
#     db: Session = Depends(get_db),
#     admin: User = Depends(get_admin_user)
# ):
#     job = db.query(Job).filter(Job.id == job_id).first()
#     if not job:
#         raise HTTPException(status_code=404, detail="Job not found")

#     job.title = job_data.title
#     job.description = job_data.description
#     job.skills_required = ",".join(job_data.skills_required)
#     job.experience_required = job_data.experience_required
#     db.commit()
#     db.refresh(job)
#     return job

# @router.delete("/{job_id}")
# def delete_job(
#     job_id: int,
#     db: Session = Depends(get_db),
#     admin: User = Depends(get_admin_user)
# ):
#     job = db.query(Job).filter(Job.id == job_id).first()
#     if not job:
#         raise HTTPException(status_code=404, detail="Job not found")
#     db.delete(job)
#     db.commit()
#     return {"message": "Job deleted successfully"}
from fastapi import APIRouter

router = APIRouter(
    prefix="/jobs",
    tags=["Jobs"]
)

@router.get("/")
def get_jobs():
    return {"message": "All jobs"}
