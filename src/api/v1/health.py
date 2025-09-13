"""Health check endpoint."""

from fastapi import APIRouter
from datetime import datetime
from src.db.base import engine
from src.db.redis_client import redis_client
from sqlalchemy import text

router = APIRouter()


@router.get("/health")
async def health_check():
    """Health check endpoint."""
    health_status = {
        "status": "healthy",
        "timestamp": datetime.utcnow().isoformat(),
        "services": {}
    }

    # Check PostgreSQL
    try:
        with engine.connect() as conn:
            conn.execute(text("SELECT 1"))
        health_status["services"]["postgres"] = "healthy"
    except Exception as e:
        health_status["services"]["postgres"] = f"unhealthy: {str(e)}"
        health_status["status"] = "degraded"

    # Check Redis
    try:
        if redis_client.ping():
            health_status["services"]["redis"] = "healthy"
        else:
            health_status["services"]["redis"] = "unhealthy"
            health_status["status"] = "degraded"
    except Exception as e:
        health_status["services"]["redis"] = f"unhealthy: {str(e)}"
        health_status["status"] = "degraded"

    return health_status