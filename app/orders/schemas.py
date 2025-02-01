from datetime import datetime

from pydantic import BaseModel


class OrderResponseSchema(BaseModel):
    date: datetime
    movies: list[str]
    total_amount: float
    status: str
