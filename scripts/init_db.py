#!/usr/bin/env python
"""Initialize database with tables and sample data."""

import sys
import os
from pathlib import Path

# Add project root to path
sys.path.append(str(Path(__file__).parent.parent))

from src.db.base import Base, engine
from src.db.models import *
from sqlalchemy.orm import Session
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def create_tables():
    """Create all database tables."""
    logger.info("Creating database tables...")
    Base.metadata.create_all(bind=engine)
    logger.info("Database tables created successfully!")


def drop_tables():
    """Drop all database tables."""
    logger.info("Dropping existing tables...")
    Base.metadata.drop_all(bind=engine)
    logger.info("Tables dropped successfully!")


def init_sample_data():
    """Initialize database with sample data."""
    from src.db.base import SessionLocal
    from passlib.context import CryptContext

    pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

    db = SessionLocal()
    try:
        # Create sample user
        sample_user = User(
            email="test@tldrify.com",
            username="testuser",
            hashed_password=pwd_context.hash("test123"),
            is_active=True,
            is_superuser=False
        )

        db.add(sample_user)
        db.commit()
        logger.info("Sample data created successfully!")

    except Exception as e:
        logger.error(f"Error creating sample data: {e}")
        db.rollback()
    finally:
        db.close()


def main():
    """Main initialization function."""
    import argparse

    parser = argparse.ArgumentParser(description="Database initialization script")
    parser.add_argument("--drop", action="store_true", help="Drop existing tables")
    parser.add_argument("--sample", action="store_true", help="Create sample data")
    args = parser.parse_args()

    if args.drop:
        response = input("Are you sure you want to drop all tables? (yes/no): ")
        if response.lower() == "yes":
            drop_tables()
        else:
            logger.info("Operation cancelled.")
            return

    create_tables()

    if args.sample:
        init_sample_data()

    logger.info("Database initialization complete!")


if __name__ == "__main__":
    main()