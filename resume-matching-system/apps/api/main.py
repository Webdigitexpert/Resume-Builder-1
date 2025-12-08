from fastapi import FastAPI, UploadFile, File, Form, Response, HTTPException, Depends
from fastapi.responses import JSONResponse
from pydantic import BaseModel, ConfigDict
import os, uuid
from typing import Optional


# ML / NLP services
from libs.service.resume_parser import parse_resume_to_text, extract_details
from libs.service.jd_parser import parse_job_description
from libs.service.embedding_service import generate_embeddings
from libs.service.match_scoring import calculate_similarity_score, skill_gap_analysis
from libs.service.pdf_service import export_score_pdf

# Routers from services
from apps.services.user_services.app.index import router as user_router
from apps.services.admin_services.app.index import router as admin_router
from apps.services.match_services.app.routes.match_routes import router as match_router
from apps.services.match_services.app.routes.upload_routes import router as upload_router
from apps.services.user_services.app.routes.auth_routes import router as auth_router

from resources.auth.dependencies import get_current_user, get_admin_user

from resources.database.base import Base
from resources.database.session import engine


from starlette.middleware import Middleware
from starlette.middleware.base import BaseHTTPMiddleware

from sqlalchemy.orm import Session
from fastapi import Depends
from resources.database.session import get_db

from apps.services.match_services.app.models.match_models import MatchResult

from apps.services.match_services.app.models.upload_model import Resume, JobDescription
from libs.service.jd_parser import parse_job_description

from libs.service.resume_extractor import extract_resume_details



app = FastAPI(title="Resume Matching System API")

# create tables
Base.metadata.create_all(bind=engine)

# === include microservice routers ===
app.include_router(auth_router)
# ---------- ML Request Models ----------

# Protected routes
app.include_router(user_router, dependencies=[Depends(get_current_user)])
app.include_router(admin_router, dependencies=[Depends(get_admin_user)])
app.include_router(match_router, dependencies=[Depends(get_current_user)])
app.include_router(upload_router, dependencies=[Depends(get_current_user)])

class MatchRequest(BaseModel):
    resume_id: str
    jd_id: str

class ExportPdfDto(BaseModel):
    match_id: str
# ---------- Middleware for file size limit ----------

class MatchDTO(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    



class LimitUploadSize(BaseHTTPMiddleware):
    async def dispatch(self, request, call_next):
        if int(request.headers.get("content-length", 0)) > 1024 * 1024 * 20:  # 20 MB limit
            return JSONResponse({"detail": "File too large"}, status_code=413)
        return await call_next(request)

app.add_middleware(LimitUploadSize)
# ---------- Core Endpoints ----------

@app.on_event("startup")
async def startup_event():
    print("\n🚀 Server is running at: http://127.0.0.1:8000")
    print("📌 Swagger Docs: http://127.0.0.1:8000/docs\n")



@app.post("/upload/resume")
async def upload_resume(
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
):
    os.makedirs("temp", exist_ok=True)

    contents = await file.read()
    temp_path = os.path.join("temp", file.filename)

    # Save uploaded file
    with open(temp_path, "wb") as f:
        f.write(contents)

    # Extract text safely
    try:
        text = parse_resume_to_text(temp_path)
    except Exception as e:
        raise HTTPException(
            status_code=400,
            detail=f"Error extracting text: {str(e)}"
        )

    # Ensure text exists
    if not text or not text.strip():
        raise HTTPException(
            status_code=400,
            detail="Unable to extract text from resume."
        )

    # Extract structured info from resume
    extracted = extract_details(text)

    # Unpack details
    skills = extracted["skills"]
    name = extracted["name"]
    email = extracted["email"]
    phone = extracted["phone"]
    years = extracted["experience"]["years"]
    months = extracted["experience"]["months"]

    # Save into DB
    resume = Resume(
        file_name=file.filename,
        text=text,
        candidate_name=name,
        candidate_email=email,
        candidate_phone=phone,
        years_of_experience=years,
        months_of_experience=months,
        user_id=current_user.id
    )

    db.add(resume)
    db.commit()
    db.refresh(resume)

    return {
        "resume_id": resume.id,
        "message": "Resume uploaded successfully",
        "extracted_details": extracted
    }




@app.post("/upload/jd")
async def upload_jd(
    text: Optional[str] = Form(None),
    file: Optional[UploadFile] = File(None)
):
    # Case 1: TEXT ONLY
    if text and not file:
        return {
            "mode": "text_only",
            "received_text": text
        }

    # Case 2: FILE ONLY
    if file and not text:
        contents = await file.read()
        return {
            "mode": "file_only",
            "file_name": file.filename,
            "file_size": len(contents)
        }

    # Case 3: BOTH TEXT + FILE
    if file and text:
        contents = await file.read()
        return {
            "mode": "text_and_file",
            "received_text": text,
            "file_name": file.filename,
            "file_size": len(contents)
        }

    # Case 4: Nothing provided
    return {"error": "You must send either text or file or both."}


@app.post("/match")
async def match(request: MatchRequest, db: Session = Depends(get_db),
                  user = Depends(get_current_user)):
    resume = db.query(Resume).filter(Resume.id == request.resume_id).first()
    jd = db.query(JobDescription).filter(JobDescription.id == request.jd_id).first()

    if not resume or not jd:
        raise HTTPException(status_code=404, detail="Invalid resume or JD ID")

    resume_emb = generate_embeddings(resume.text)
    jd_emb = generate_embeddings(jd.text)

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
    db.commit()
    db.refresh(result)

    return {"match_id": result.id, "score": score, "matched": matched, "missing": missing}

@app.post("/export/pdf")
async def export_pdf(data: ExportPdfDto, db: Session = Depends(get_db), user = Depends(get_current_user)):
    result = db.query(MatchResult).filter(MatchResult.id == data.match_id).first()
    if not result:
        raise HTTPException(status_code=404, detail="Match result not found")

    os.makedirs("temp", exist_ok=True)
    file_name = f"report_{result.id}.pdf"
    file_path = os.path.join("temp", file_name)

    export_score_pdf(file_path, result.score, result.matched, result.missing)

    with open(file_path, "rb") as f:
        pdf_bytes = f.read()

    return Response(
        content=pdf_bytes,
        media_type="application/pdf",
        headers={"Content-Disposition": f"attachment; filename={file_name}"}
    )