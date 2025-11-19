from pydantic import BaseModel
from typing import List, Optional

class JobCreate(BaseModel):
    title: str
    description: str
    skills_required: List[str]
    experience_required: Optional[float] = None

class JobResponse(JobCreate):
    id: int

    class Config:
        orm_mode = True
