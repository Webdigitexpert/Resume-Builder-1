from fastapi import FastAPI, UploadFile, File, Form, Response, HTTPException, Depends
from fastapi.responses import JSONResponse
from pydantic import BaseModel, ConfigDict
import os, uuid


# ML / NLP services
from libs.service.resume_parser import parse_resume_to_text, extract_skills
from libs.service.jd_parser import parse_job_description
from libs.service.embedding_service import generate_embeddings
from libs.service.match_scoring import calculate_similarity_score, skill_gap_analysis
from libs.service.pdf_service import export_score_pdf

# Routers from services
from apps.services.user_services.app.index import router as user_router
from apps.services.admin_services.app.index import router as admin_router
from apps.services.match_services.app.routes.match_routes import router as match_router
from apps.services.match_services.app.routes.upload_routes import router as upload_router



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



app = FastAPI(title="Resume Matching System API")

# create tables
Base.metadata.create_all(bind=engine)

# === include microservice routers ===
app.include_router(user_router)
app.include_router(admin_router)
app.include_router(match_router)
app.include_router(upload_router)
# ---------- ML Request Models ----------

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
async def upload_resume(file: UploadFile = File(...), db: Session = Depends(get_db)):
    os.makedirs("temp", exist_ok=True)

    contents = await file.read()
    temp_path = os.path.join("temp", file.filename)

    with open(temp_path, "wb") as f:
        f.write(contents)

    text = parse_resume_to_text(temp_path)
    skills = extract_skills(text)

    resume = Resume(file_name=file.filename, text=text)
    db.add(resume)
    db.commit()
    db.refresh(resume)

    return {"resume_id": resume.id, "message": "Resume uploaded successfully"}

@app.post("/upload/jd")
async def upload_jd(
    text: str | None = Form(None),
    file: UploadFile | None = File(None),
    db: Session = Depends(get_db)
):
    # If neither text nor file is provided
    if not text and not file:
        raise HTTPException(status_code=400, detail="Provide text or upload a PDF File")

    # If plain text provided
    if text:
        jd_text = text
        file_name = "manual-input"
    else:
        # Handle uploaded file
        os.makedirs("temp", exist_ok=True)
        contents = await file.read()
        temp_path = os.path.join("temp", file.filename)

        with open(temp_path, "wb") as f:
            f.write(contents)

        jd_text = parse_job_description(temp_path)
        file_name = file.filename

    # Save to DB
    jd = JobDescription(file_name=file_name, text=jd_text)
    db.add(jd)
    db.commit()
    db.refresh(jd)

    return {
        "jd_id": jd.id,
        "file_name": file_name,
        "text": jd_text[:300] + "..." if len(jd_text) > 300 else jd_text,
        "message": "Job Description uploaded successfully"
    }

@app.post("/match")
async def match(request: MatchRequest, db: Session = Depends(get_db)):
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
async def export_pdf(data: ExportPdfDto, db: Session = Depends(get_db)):
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