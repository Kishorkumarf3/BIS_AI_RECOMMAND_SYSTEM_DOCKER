from sqlalchemy import create_engine
from sqlalchemy.orm import declarative_base, sessionmaker
import os

from pathlib import Path

_default_db = Path(__file__).resolve().parent.parent / "bis_standards.db"
DATABASE_URL = os.getenv("DATABASE_URL", f"sqlite:///{_default_db.as_posix()}")

engine = create_engine(
    DATABASE_URL,
    connect_args={"check_same_thread": False} if DATABASE_URL.startswith("sqlite") else {},
)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
