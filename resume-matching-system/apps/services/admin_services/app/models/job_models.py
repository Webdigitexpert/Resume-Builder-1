from sqlalchemy import Column, Integer, String, Float
from resources.database.base import Base

class Job(Base):
    __tablename__ = "jobs"

    id = Column(Integer, primary_key=True, index=True)
    title = Column(String, nullable=False)
    description = Column(String, nullable=False)
    skills_required = Column(String, nullable=False)  # comma-separated
    experience_required = Column(Float, nullable=True)
