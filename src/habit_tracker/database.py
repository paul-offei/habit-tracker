"""
Database configuration and connection management.

Initializes the SQLAlchemy engine and provides a session factory.
Uses SQLite for local development, configured for thread safety.
"""

from sqlalchemy import create_engine
from sqlalchemy.orm import declarative_base, sessionmaker

# SQLite database file path. Can be overridden via environment variables later.
SQLALCHEMY_DATABASE_URL = "sqlite:///./habits.db"

# check_same_thread=False is required for SQLite when accessed across multiple threads
engine = create_engine(
    SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False}
)

# Factory for generating new database sessions
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Base class for our ORM models to inherit from
Base = declarative_base()

def init_db() -> None:
    """Creates all tables in the database if they do not exist."""
    Base.metadata.create_all(bind=engine)