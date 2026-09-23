from datetime import datetime
from typing import Generic, TypeVar

from pydantic import BaseModel, Field

T = TypeVar("T")


class HealthCheckResponse(BaseModel):
    status: str
    database: str


class MessageResponse(BaseModel):
    message: str


class TransactionCreate(BaseModel):
    account_id: str = Field(..., examples=["ACC-984211"])
    amount: float = Field(..., gt=0, examples=[249.99])
    currency: str = Field(default="USD", max_length=3, examples=["USD"])
    merchant: str = Field(..., examples=["Amazon"])
    location: str = Field(..., examples=["Dubai, UAE"])
    timestamp: datetime | None = Field(default_factory=datetime.utcnow)


class TransactionResponse(TransactionCreate):
    id: str
    created_at: datetime

    class Config:
        from_attributes = True  # Allows ORM object parsing


class Pagination(BaseModel, Generic[T]):
    items: list[T]
    total: int
    page: int
    page_size: int
