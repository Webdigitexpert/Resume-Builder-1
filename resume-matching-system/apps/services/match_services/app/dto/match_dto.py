from pydantic import BaseModel
from typing import List

class MatchCreateDto(BaseModel):
    resume_text: str
    jd_text: str
    resume_skills: List[str]
    jd_skills: List[str]

class MatchUpdateDto(BaseModel):
    score: float | None = None
    matched: list[str] | None = None
    missing: list[str] | None = None
    summary: str | None = None
