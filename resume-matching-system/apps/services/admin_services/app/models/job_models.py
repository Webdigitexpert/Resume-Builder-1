from sqlalchemy import Column, String, Integer, Text
from resources.database.base import Base
from sqlalchemy.dialects.postgresql import UUID, ARRAY
import uuid

class Job(Base):
    __tablename__ = "jobs"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    title = Column(String(255), nullable=False)
    required_skills = Column(ARRAY(String), nullable=False)
    min_experience = Column(Integer, nullable=False)
    description = Column(Text, nullable=True)
