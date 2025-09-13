#!/usr/bin/env python
"""Test database and Redis connections."""

import sys
import os
from pathlib import Path

# Add project root to path
sys.path.append(str(Path(__file__).parent.parent))

from src.db.base import engine, SessionLocal
from src.db.redis_client import redis_client
import qdrant_client
from qdrant_client import QdrantClient
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def test_postgresql():
    """Test PostgreSQL connection."""
    try:
        from sqlalchemy import text

        # Test connection
        with engine.connect() as conn:
            result = conn.execute(text("SELECT version()"))
            version = result.scalar()
            logger.info(f"✅ PostgreSQL connected: {version}")

        # Test session
        db = SessionLocal()
        db.execute(text("SELECT 1"))
        db.close()
        logger.info("✅ PostgreSQL session works")
        return True

    except Exception as e:
        logger.error(f"❌ PostgreSQL connection failed: {e}")
        return False


def test_redis():
    """Test Redis connection."""
    try:
        # Test ping
        if redis_client.ping():
            logger.info("✅ Redis connected")

            # Test set/get
            redis_client.set("test_key", "test_value", expire=10)
            value = redis_client.get("test_key")

            if value == "test_value":
                logger.info("✅ Redis set/get works")
                redis_client.delete("test_key")
                return True
            else:
                logger.error("❌ Redis set/get failed")
                return False
        else:
            logger.error("❌ Redis ping failed")
            return False

    except Exception as e:
        logger.error(f"❌ Redis connection failed: {e}")
        return False


def test_qdrant():
    """Test Qdrant connection."""
    try:
        # Connect to Qdrant
        client = QdrantClient(
            host=os.getenv("QDRANT_HOST", "localhost"),
            port=int(os.getenv("QDRANT_PORT", 6333))
        )

        # Get collections
        collections = client.get_collections()
        logger.info(f"✅ Qdrant connected: {len(collections.collections)} collections")

        return True

    except Exception as e:
        logger.error(f"❌ Qdrant connection failed: {e}")
        return False


def main():
    """Run all connection tests."""
    logger.info("="*50)
    logger.info("Testing Database Connections")
    logger.info("="*50)

    results = {
        "PostgreSQL": test_postgresql(),
        "Redis": test_redis(),
        "Qdrant": test_qdrant(),
    }

    logger.info("="*50)
    logger.info("Test Results:")
    logger.info("="*50)

    for service, status in results.items():
        status_emoji = "✅" if status else "❌"
        logger.info(f"{status_emoji} {service}: {'Connected' if status else 'Failed'}")

    # Return success if all services are connected
    all_connected = all(results.values())

    if all_connected:
        logger.info("\n🎉 All services are connected successfully!")
    else:
        logger.error("\n⚠️ Some services failed to connect. Please check Docker containers.")

    return 0 if all_connected else 1


if __name__ == "__main__":
    sys.exit(main())