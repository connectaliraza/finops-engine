from contextlib import asynccontextmanager

from database import Base, engine, get_db
from fastapi import Depends, FastAPI, HTTPException, Query, status
from models import Transaction
from schemas import (
    HealthCheckResponse,
    MessageResponse,
    Pagination,
    TransactionCreate,
    TransactionResponse,
)
from sqlalchemy import func, select, text
from sqlalchemy.ext.asyncio import AsyncSession


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup: Create tables if they don't exist
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield
    # Shutdown: Clean up database engine
    await engine.dispose()


app = FastAPI(
    title="FinOps API",
    description="API for FinOps application",
    version="1.0.0",
    lifespan=lifespan,
)


@app.get("/", response_model=MessageResponse)
def root():
    return MessageResponse(message="Welcome to the FinOps API")


@app.get("/health", response_model=HealthCheckResponse)
async def health_check(db: AsyncSession = Depends(get_db)):
    try:
        # Execute a simple query to check database connectivity
        await db.execute(text("SELECT 1"))
        return HealthCheckResponse(status="ok", database="connected")
    except Exception as e:
        return HealthCheckResponse(status="error", database=str(e))


@app.post(
    "/transactions/",
    response_model=TransactionResponse,
    status_code=status.HTTP_201_CREATED,
)
async def create_transaction(
    payload: TransactionCreate, db: AsyncSession = Depends(get_db)
):
    try:
        new_transaction = Transaction(**payload.model_dump())
        db.add(new_transaction)
        await db.commit()
        await db.refresh(new_transaction)
        return new_transaction
    except Exception as e:
        await db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Database write error: {str(e)}",
        )


@app.get("/transactions/{transaction_id}", response_model=TransactionResponse)
async def get_transaction(
    transaction_id: str, db: AsyncSession = Depends(get_db)
):
    result = await db.execute(
        select(Transaction).where(Transaction.id == transaction_id)
    )
    transaction = result.scalar_one_or_none()
    if transaction is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Transaction not found",
        )
    return transaction


@app.get(
    "/accounts/{account_id}/transactions",
    response_model=Pagination[TransactionResponse],
)
async def list_account_transactions(
    account_id: str,
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=20, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
):
    filters = Transaction.account_id == account_id
    total = await db.scalar(
        select(func.count()).select_from(Transaction).where(filters)
    )
    result = await db.execute(
        select(Transaction)
        .where(filters)
        .order_by(Transaction.timestamp.desc(), Transaction.id.desc())
        .offset((page - 1) * page_size)
        .limit(page_size)
    )
    return Pagination[TransactionResponse](
        items=list(result.scalars().all()),
        total=total or 0,
        page=page,
        page_size=page_size,
    )
