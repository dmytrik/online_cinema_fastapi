from datetime import datetime

from pydantic import BaseModel


class OrderCreateResponseSchema(BaseModel):
    date: datetime
    movies: list[str]
    total_amount: float
    status: str
    pay_here: str


class OrderListResponseSchema(BaseModel):
    date: datetime
    movies: list[str]
    total_amount: float
    status: str

class OrderRefundResponseSchema(BaseModel):
    message: str
