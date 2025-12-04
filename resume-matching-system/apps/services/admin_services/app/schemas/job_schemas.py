from pydantic import BaseModel
from typing import List, Optional

class JobCreate(BaseModel):
    title: str
    required_skills: list[str]
    min_experience: int
    description: str


class JobResponse(JobCreate):
    id: str

    class Config:
        orm_mode = True