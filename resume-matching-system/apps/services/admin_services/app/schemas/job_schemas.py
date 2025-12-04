from pydantic import BaseModel
import sqlalchemy.dialects.postgresql
from typing import List, Optional
from uuid import UUID

class JobCreate(BaseModel):
    title: str
    required_skills: list[str]
    min_experience: int
    description: str


class JobResponse(JobCreate):
    id: UUID

    class Config:
        orm_mode = True