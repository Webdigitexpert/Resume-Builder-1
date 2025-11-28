from sqlalchemy import Column, String, Text
from resources.database.base import Base
import uuid





class Resume(Base):
    __tablename__ = "resumes"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    file_name = Column(String, nullable=False)
    text = Column(Text, nullable=False)

class JobDescription(Base):
    __tablename__ = "job_descriptions"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    file_name = Column(String, nullable=True)
    text = Column(Text, nullable=False)
    

