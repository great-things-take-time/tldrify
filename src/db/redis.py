"""Redis client configuration."""

import os
import logging
import redis
from typing import Optional

logger = logging.getLogger(__name__)

# Redis configuration
REDIS_URL = os.getenv("REDIS_URL", "redis://localhost:6379/0")

# Initialize Redis client
redis_client: Optional[redis.Redis] = None

try:
    redis_client = redis.from_url(REDIS_URL, decode_responses=True)
    # Test connection
    redis_client.ping()
    logger.info(f"Connected to Redis at {REDIS_URL}")
except redis.ConnectionError as e:
    logger.warning(f"Could not connect to Redis: {e}. Caching will be disabled.")
    redis_client = None
except Exception as e:
    logger.error(f"Redis initialization error: {e}")
    redis_client = None


def get_redis_client() -> Optional[redis.Redis]:
    """Get Redis client instance."""
    return redis_client


def is_redis_available() -> bool:
    """Check if Redis is available."""
    if redis_client:
        try:
            redis_client.ping()
            return True
        except:
            return False
    return False