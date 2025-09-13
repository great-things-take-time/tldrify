"""Redis client configuration and utilities."""

import redis
from redis import ConnectionPool
import json
import os
from typing import Optional, Any, Dict
from dotenv import load_dotenv

load_dotenv()


class RedisClient:
    """Redis client wrapper with connection pooling."""

    def __init__(self):
        self.pool = ConnectionPool(
            host=os.getenv("REDIS_HOST", "localhost"),
            port=int(os.getenv("REDIS_PORT", 6379)),
            db=int(os.getenv("REDIS_DB", 0)),
            max_connections=50,
            decode_responses=True,
        )
        self.client = redis.Redis(connection_pool=self.pool)

    def get(self, key: str) -> Optional[str]:
        """Get value from Redis."""
        try:
            return self.client.get(key)
        except redis.RedisError as e:
            print(f"Redis GET error: {e}")
            return None

    def set(self, key: str, value: Any, expire: Optional[int] = None) -> bool:
        """Set value in Redis with optional expiration."""
        try:
            if isinstance(value, (dict, list)):
                value = json.dumps(value)
            return self.client.set(key, value, ex=expire)
        except redis.RedisError as e:
            print(f"Redis SET error: {e}")
            return False

    def delete(self, key: str) -> bool:
        """Delete key from Redis."""
        try:
            return bool(self.client.delete(key))
        except redis.RedisError as e:
            print(f"Redis DELETE error: {e}")
            return False

    def exists(self, key: str) -> bool:
        """Check if key exists in Redis."""
        try:
            return bool(self.client.exists(key))
        except redis.RedisError as e:
            print(f"Redis EXISTS error: {e}")
            return False

    def get_json(self, key: str) -> Optional[Dict]:
        """Get JSON value from Redis."""
        value = self.get(key)
        if value:
            try:
                return json.loads(value)
            except json.JSONDecodeError:
                return None
        return None

    def set_json(self, key: str, value: Dict, expire: Optional[int] = None) -> bool:
        """Set JSON value in Redis."""
        return self.set(key, json.dumps(value), expire)

    def incr(self, key: str) -> Optional[int]:
        """Increment counter in Redis."""
        try:
            return self.client.incr(key)
        except redis.RedisError as e:
            print(f"Redis INCR error: {e}")
            return None

    def set_progress(self, job_id: str, progress: Dict) -> bool:
        """Set job progress in Redis."""
        key = f"job:progress:{job_id}"
        return self.set_json(key, progress, expire=3600)  # Expire after 1 hour

    def get_progress(self, job_id: str) -> Optional[Dict]:
        """Get job progress from Redis."""
        key = f"job:progress:{job_id}"
        return self.get_json(key)

    def cache_embedding(self, text_hash: str, embedding: list, expire: int = 86400) -> bool:
        """Cache embedding vector in Redis."""
        key = f"embedding:{text_hash}"
        return self.set_json(key, embedding, expire)

    def get_cached_embedding(self, text_hash: str) -> Optional[list]:
        """Get cached embedding from Redis."""
        key = f"embedding:{text_hash}"
        return self.get_json(key)

    def ping(self) -> bool:
        """Check Redis connection."""
        try:
            return self.client.ping()
        except redis.RedisError:
            return False


# Global Redis client instance
redis_client = RedisClient()