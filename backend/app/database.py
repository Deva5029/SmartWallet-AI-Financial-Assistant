# This file sets up the database connection and session management using SQLAlchemy.

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base
from .config import settings

# Create the SQLAlchemy engine to connect to the PostgreSQL database.
engine = create_engine(
    settings.DATABASE_URL,
)

# Create a SessionLocal class, which will be our actual database session.
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Create a Base class. Our ORM models will inherit from this class.
Base = declarative_base()

# Dependency to get a DB session for each request
def get_db():
    """
    This function is a FastAPI dependency that provides a database session
    to the API endpoints. It ensures that the database session is always

    closed after the request is finished.
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()