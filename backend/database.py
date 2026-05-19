from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from dotenv import load_dotenv
import os

load_dotenv(dotenv_path=os.path.join(os.path.dirname(__file__), '.env'))


_RAW_URL = os.getenv(
    "DATABASE_URL",
    "postgresql://postgres:dmbjsnzy@localhost:5432/taskrpg"
)

# Use psycopg v3 driver to avoid Windows encoding issues with psycopg2
DATABASE_URL = _RAW_URL.replace("postgresql://", "postgresql+psycopg://", 1)

engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
