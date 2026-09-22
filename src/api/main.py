from database import get_db
from fastapi import Depends, FastAPI
from schemas import HealthCheckResponse, MessageResponse
from sqlalchemy import text
from sqlalchemy.orm import Session

app = FastAPI(
    title="FinOps API",
    description="API for FinOps application",
    version="1.0.0",
)


@app.get("/", response_model=MessageResponse)
def root():
    return MessageResponse(message="Welcome to the FinOps API")


@app.get("/health", response_model=HealthCheckResponse)
def health_check(db: Session = Depends(get_db)):
    try:
        # Execute a simple query to check database connectivity
        db.execute(text("SELECT 1"))
        return HealthCheckResponse(status="ok", database="connected")
    except Exception as e:
        return HealthCheckResponse(status="error", database=str(e))
