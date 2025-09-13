"""Database dependencies for FastAPI with SQLAlchemy 2.x best practices."""

from typing import Annotated, AsyncGenerator, Generator
from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker, AsyncEngine
from sqlalchemy.orm import Session
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import NullPool, QueuePool
import os
from dotenv import load_dotenv

load_dotenv()

# Database URLs
DATABASE_URL = os.getenv("DATABASE_URL", "postgresql+psycopg://tldrify_user:tldrify_pass_2024@localhost:5432/tldrify_db")
ASYNC_DATABASE_URL = os.getenv(
    "ASYNC_DATABASE_URL",
    DATABASE_URL.replace("postgresql+psycopg://", "postgresql+asyncpg://")
)

# ============= Synchronous Database Setup =============
# Keep for backward compatibility and gradual migration

sync_engine = create_engine(
    DATABASE_URL,
    poolclass=QueuePool,
    pool_size=10,
    max_overflow=20,
    pool_pre_ping=True,
    echo=False,
    future=True,  # SQLAlchemy 2.0 style
)

SyncSessionLocal = sessionmaker(
    bind=sync_engine,
    autocommit=False,
    autoflush=False,
    expire_on_commit=False,  # Better for async operations
)

def get_sync_db() -> Generator[Session, None, None]:
    """Dependency for synchronous database session."""
    with SyncSessionLocal() as session:
        try:
            yield session
        except Exception:
            session.rollback()
            raise
        finally:
            session.close()

# ============= Asynchronous Database Setup =============
# SQLAlchemy 2.x best practice for async operations

async_engine: AsyncEngine = create_async_engine(
    ASYNC_DATABASE_URL,
    poolclass=NullPool,  # Recommended for async
    echo=False,
    future=True,
)

AsyncSessionLocal = async_sessionmaker(
    bind=async_engine,
    class_=AsyncSession,
    autocommit=False,
    autoflush=False,
    expire_on_commit=False,
)

async def get_async_db() -> AsyncGenerator[AsyncSession, None]:
    """Dependency for asynchronous database session."""
    async with AsyncSessionLocal() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()

# ============= Type Aliases for Dependency Injection =============
# FastAPI best practice: Use Annotated for cleaner dependency declarations

# Synchronous session dependency
DBSession = Annotated[Session, Depends(get_sync_db)]

# Asynchronous session dependency
AsyncDBSession = Annotated[AsyncSession, Depends(get_async_db)]

# ============= Database Lifecycle Management =============

async def init_async_db():
    """Initialize async database (create tables, etc.)."""
    # This would be called during app startup
    pass

async def close_async_db():
    """Close async database connections."""
    await async_engine.dispose()

def init_sync_db():
    """Initialize sync database (create tables, etc.)."""
    # This would be called during app startup
    pass

def close_sync_db():
    """Close sync database connections."""
    sync_engine.dispose()