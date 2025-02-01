from sqlalchemy import DateTime

from pydantic import BaseModel


class OrderResponseSchema(BaseModel):
    date: DateTime
    movies: list[str]
    total_amount: float
    status: str
