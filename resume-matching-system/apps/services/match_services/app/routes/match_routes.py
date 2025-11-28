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

