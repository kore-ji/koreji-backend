from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.ext.declarative import declarative_base
import os

# Prefer DATABASE_URL environment variable (set in docker-compose)
DATABASE_URL = os.getenv("DATABASE_URL", "postgresql://koreji:koreji_password@localhost:5432/koreji_db")

engine = create_engine(DATABASE_URL)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()