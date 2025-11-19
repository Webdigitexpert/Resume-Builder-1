from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from .base import Base

DATABASE_URL = "postgresql://postgres:Admin%40123@localhost:5432/resume_db"

engine = create_engine(DATABASE_URL, future=True)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
