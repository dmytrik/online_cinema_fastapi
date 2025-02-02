from datetime import datetime
from pydantic import BaseModel


class PaymentResponseSchema(BaseModel):
    date: datetime
    amount: float
    status: str


class PaymentSuccessSchema(BaseModel):
    message: str
    amount_paid: float
    currency: str


class PaymentCancelSchema(BaseModel):
    message: str
    pay_here: str
    amount_paid: float
    currency: str
