"""Database base configuration and session management."""

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base
from sqlalchemy.pool import NullPool, QueuePool
from typing import Generator
import os
from dotenv import load_dotenv

load_dotenv()

DATABASE_URL = os.getenv("DATABASE_URL", "postgresql+psycopg://tldrify_user:tldrify_pass_2024@localhost:5432/tldrify_db")

# Create engine with connection pooling
# Using future=True for SQLAlchemy 2.0 compatibility
engine = create_engine(
    DATABASE_URL,
    poolclass=QueuePool,
    pool_size=10,
    max_overflow=20,
    pool_pre_ping=True,  # Verify connections before using
    echo=False,  # Set to True for SQL query logging
    future=True,  # Enable SQLAlchemy 2.0 style
)

# Create session factory with SQLAlchemy 2.x best practices
SessionLocal = sessionmaker(
    bind=engine,
    autocommit=False,
    autoflush=False,
    expire_on_commit=False,  # Better for performance
)

# Create base class for models using SQLAlchemy 2.x style
Base = declarative_base()

def get_db() -> Generator:
    """Get database session with proper exception handling."""
    with SessionLocal() as session:
        try:
            yield session
        except Exception:
            session.rollback()
            raise
        finally:
            session.close()

# Export new dependencies for gradual migration
# Commented out to avoid circular import issues
# from .dependencies import (
#     DBSession,
#     AsyncDBSession,
#     get_sync_db,
#     get_async_db,
#     async_engine,
#     AsyncSessionLocal,
# )