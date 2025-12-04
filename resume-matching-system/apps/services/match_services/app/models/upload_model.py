
from resources.database.base import Base
import uuid
from sqlalchemy import Column, String, Integer, Float, Text, ForeignKey, DateTime
from sqlalchemy.orm import relationship
from datetime import datetime
from resources.database.base import Base
import uuid





class Resume(Base):
    __tablename__ = "resumes"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    file_name = Column(String, nullable=False)
    text = Column(Text, nullable=False)
    
    # NEW FIELDS
    candidate_name = Column(String, nullable=True)
    candidate_email = Column(String, nullable=True)
    candidate_phone = Column(String, nullable=True)
    years_of_experience = Column(Float, nullable=True)

    # Optional: link to User
    user_id = Column(String, ForeignKey("users.id"), nullable=True)

class JobDescription(Base):
    __tablename__ = "job_descriptions"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    file_name = Column(String, nullable=True)
    text = Column(Text, nullable=False)
   
class JobApplication(Base):
    __tablename__ = "job_applications"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    job_id = Column(Integer, ForeignKey("jobs.id"), nullable=False)   # ✅ FIXED
    resume_id = Column(String, ForeignKey("resumes.id"), nullable=False)
    user_id = Column(String, ForeignKey("users.id"), nullable=True)
    applied_at = Column(DateTime, default=datetime.utcnow)
 

