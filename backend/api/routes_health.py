from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from sqlalchemy import text

from backend.database.connection import get_db
from backend.ai.engine import ai_engine
from backend.models.schemas import HealthResponse

router = APIRouter(prefix="/api/health", tags=["Health & Diagnostics"])

@router.get("", response_model=HealthResponse)
def health_check(db: Session = Depends(get_db)):
    """Verifies backend health, database connectivity, and central AI engine status."""
    try:
        db.execute(text("SELECT 1"))
        db_status = "connected"
    except Exception as exc:
        db_status = f"unhealthy: {str(exc)}"

    ai_status = ai_engine.get_status()

    return HealthResponse(
        status="healthy" if db_status == "connected" else "degraded",
        project="KrushiSetu",
        version="1.0.0",
        database=db_status,
        ai_engine_ready=bool(ai_status.get("dataset_connectors_ready")),
    )

