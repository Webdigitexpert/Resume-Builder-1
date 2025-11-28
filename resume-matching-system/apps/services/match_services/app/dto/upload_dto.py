from pydantic import BaseModel

class ResumeUpdateDto(BaseModel):
    text: str | None = None
    file_name: str | None = None

class JDUpdateDto(BaseModel):
    text: str | None = None
    file_name: str | None = None
