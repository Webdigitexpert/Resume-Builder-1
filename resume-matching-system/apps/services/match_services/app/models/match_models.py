from sqlalchemy import Column, String, Float, JSON
from resources.database.base import Base
import uuid

from sqlalchemy import Column, Integer, Float, String, ForeignKey
from sqlalchemy.dialects.postgresql import ARRAY
from sqlalchemy.orm import relationship
from resources.database.base import Base   # update path if different


class MatchResult(Base):
    __tablename__ = "match_results"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    score = Column(Float, nullable=False)
    matched = Column(JSON, nullable=False)
    missing = Column(JSON, nullable=False)
    summary = Column(String, nullable=False)

class MatchResult(Base):
    __tablename__ = "match_results"
    __table_args__ = {"extend_existing": True}

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    score = Column(Float)
    matched = Column(ARRAY(String))
    missing = Column(ARRAY(String))
    summary = Column(String)

    resume_id = Column(String, ForeignKey("resumes.id"))
    jd_id = Column(String, ForeignKey("job_descriptions.id"))

