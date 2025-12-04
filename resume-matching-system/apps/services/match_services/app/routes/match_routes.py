from fastapi import APIRouter, HTTPException, Depends
from sqlalchemy.orm import Session
from fastapi.responses import FileResponse
import os
from sqlalchemy import select

from apps.services.match_services.app.models.match_models import MatchResult
from apps.services.match_services.app.models.upload_model import Resume, JobDescription
from resources.database.session import get_db

from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.lib.pagesizes import LETTER
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
from reportlab.lib import colors

from resources.auth.dependencies import get_current_user
from apps.services.user_services.app.models.user_model import User

router = APIRouter(prefix="/match", tags=["Match Results"])

@router.get("/{result_id}")
async def get_match(result_id: str, db: Session = Depends(get_db)):
    result = db.query(MatchResult).filter(MatchResult.id == result_id).first()
    if not result:
        raise HTTPException(status_code=404, detail="Result not found")
    return result

@router.get("/all")
async def get_all_matches(db: Session = Depends(get_db)):
    results = db.query(MatchResult).all()
    return results

@router.get("/my-matches")
async def get_my_matches(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    # join MatchResult -> Resume (by resume_id -> resumes.id -> user_id)
    results = (
        db.query(MatchResult)
        .join(Resume, MatchResult.resume_id == Resume.id)
        .filter(Resume.user_id == current_user.id)
        .all()
    )
    return results

@router.get("/job-report/{jd_id}")
async def generate_job_report(jd_id: str, db: Session = Depends(get_db)):
    jd = db.query(JobDescription).filter(JobDescription.id == jd_id).first()
    if not jd:
        raise HTTPException(status_code=404, detail="Job not found")

    matches = (
        db.query(MatchResult)
        .join(Resume, MatchResult.resume_id == Resume.id)
        .filter(MatchResult.jd_id == jd_id)
        .all()
    )

    if not matches:
        raise HTTPException(status_code=404, detail="No matches found for this job")

    ranked = sorted(matches, key=lambda m: m.score, reverse=True)

    os.makedirs("reports", exist_ok=True)
    file_path = f"reports/job_report_{jd_id}.pdf"

    styles = getSampleStyleSheet()
    doc = SimpleDocTemplate(file_path, pagesize=LETTER)
    story = []

    # Title
    story.append(Paragraph("Job Match Report", styles["Title"]))
    story.append(Spacer(1, 12))

    # Job section
    story.append(Paragraph("Job Details", styles["Heading2"]))
    story.append(Paragraph(f"Job ID: {jd_id}", styles["Normal"]))
    story.append(Paragraph(f"Job File: {jd.file_name}", styles["Normal"]))
    story.append(Spacer(1, 12))

    # Table header
    table_data = [["Rank", "Candidate", "Email", "Score", "Matched Skills", "Missing Skills", "Status"]]

    rank = 1
    for m in ranked:
        resume = db.query(Resume).filter(Resume.id == m.resume_id).first()
        matched_str = ", ".join(m.matched[:5])
        missing_str = ", ".join(m.missing[:5])
        status = "Shortlist" if m.score >= 70 else "Review"

        table_data.append([
            rank,
            resume.candidate_name or resume.file_name,
            resume.candidate_email or "-",
            f"{m.score:.2f}%",
            matched_str,
            missing_str,
            status
        ])
        rank += 1

    tbl = Table(table_data, repeatRows=1)
    tbl.setStyle(TableStyle([
        ("BACKGROUND", (0,0), (-1,0), colors.lightgrey),
        ("GRID", (0,0), (-1,-1), 0.5, colors.grey),
        ("FONTNAME", (0,0), (-1,0), "Helvetica-Bold"),
        ("FONTSIZE", (0,0), (-1,-1), 8),
        ("ALIGN", (0,0), (0,-1), "CENTER"),
        ("VALIGN", (0,0), (-1,-1), "TOP"),
    ]))

    story.append(tbl)
    story.append(Spacer(1, 12))

    story.append(Paragraph(
        "Note: Candidates with status 'Shortlist' are recommended based on match score.",
        styles["Italic"]
    ))

    doc.build(story)

    return FileResponse(
        file_path,
        media_type="application/pdf",
        filename=f"job_report_{jd_id}.pdf"
    )

