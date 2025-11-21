from fastapi import FastAPI, UploadFile, File, Form, Response, HTTPException, Depends
from fastapi.responses import JSONResponse
from pydantic import BaseModel
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



from resources.database.base import Base
from resources.database.session import engine

from starlette.middleware import Middleware
from starlette.middleware.base import BaseHTTPMiddleware


app = FastAPI(title="Resume Matching System API")

# create tables
Base.metadata.create_all(bind=engine)

# === include microservice routers ===
app.include_router(user_router)
app.include_router(admin_router)

# ---------- ML Request Models ----------

class MatchRequest(BaseModel):
    resume_text: str
    jd_text: str
    resume_skills: list[str]
    jd_skills: list[str]


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
async def upload_resume(file: UploadFile = File(...)):
    os.makedirs("temp", exist_ok=True)

    contents = await file.read()
    temp_path = os.path.join("temp", file.filename)

    with open(temp_path, "wb") as f:
        f.write(contents)

    text = parse_resume_to_text(temp_path)
    skills = extract_skills(text)

    return {"text": text, "skills": skills}

@app.post("/upload/jd")
async def upload_jd(
    text: str | None = Form(None),
    file: UploadFile | None = File(None)
):
    # If neither text nor file is provided
    if not text and not file:
        raise HTTPException(status_code=400, detail="Provide Job Description text or upload a file")

    # If JD text exists
    if text:
        jd_text = text
    else:
        # Process uploaded file
        os.makedirs("temp", exist_ok=True)
        contents = await file.read()
        temp_path = os.path.join("temp", file.filename)

        with open(temp_path, "wb") as f:
            f.write(contents)

        jd_text = parse_job_description(temp_path)

    return {"jd_text": jd_text}

@app.post("/match")
async def match(request: MatchRequest):
    resume_emb = generate_embeddings(request.resume_text)
    jd_emb = generate_embeddings(request.jd_text)

    score = calculate_similarity_score(resume_emb, jd_emb)
    matched, missing = skill_gap_analysis(request.resume_skills, request.jd_skills)

    return {
        "score": score,
        "matched": matched,
        "missing": missing,
        "summary": f"Candidate fits {score:.2f}% of the JD requirements",
    }

@app.post("/export/pdf")
async def export_pdf(score: float, matched: list[str], missing: list[str]):
    os.makedirs("temp", exist_ok=True)
    file_name = f"report_{uuid.uuid4()}.pdf"
    file_path = os.path.join("temp", file_name)

    export_score_pdf(file_path, score, matched, missing)

    with open(file_path, "rb") as f:
        pdf_bytes = f.read()

    return Response(
        content=pdf_bytes,
        media_type="application/pdf",
        headers={"Content-Disposition": f"attachment; filename={file_name}"},
    )
