from datetime import date

import stripe
from fastapi import APIRouter, status, Depends, HTTPException, BackgroundTasks
from sqlalchemy import func
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session

from app.accounts.models import UserModel
from app.cart.models import Purchases
from app.orders.models import OrderModel
from app.payments.models import PaymentModel
from app.payments.schemas import PaymentResponseSchema, PaymentSuccessSchema, PaymentCancelSchema
from core.database import get_db
from core.dependencies import get_jwt_auth_manager
from core.config import settings
from exceptions import BaseSecurityError
from security.http import get_token
from security.interfaces import JWTAuthManagerInterface
from app.accounts.email_service import send_email


router = APIRouter()


stripe.api_key = settings.STRIPE_SECRET_KEY


@router.get("/", response_model=list[PaymentResponseSchema], status_code=status.HTTP_200_OK)
def get_payments(
        id_user: int = None,
        payment_date: date = None,
        payment_status: str = None,
        db: Session = Depends(get_db),
        token: str = Depends(get_token),
        jwt_manager: JWTAuthManagerInterface = Depends(get_jwt_auth_manager)
):
    try:
        payload = jwt_manager.decode_access_token(token)
        user_id = payload.get("user_id")
    except BaseSecurityError as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=str(e)
        )

    user = db.query(UserModel).filter_by(id=user_id).first()

    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
        )

    payments = db.query(PaymentModel)

    if user.group.name == "admin":
        if id_user:
            payments = payments.filter_by(user_id=id_user)
        if payment_date:
            payments = payments.filter(func.DATE(PaymentModel.created_at) == payment_date)
        if payment_status:
            payments = payments.filter_by(status=payment_status)
    else:
        payments = payments.filter_by(user_id=user.id)

    return [
        {
            "date": payment.created_at,
            "amount": payment.amount,
            "status": payment.status
        }
        for payment in payments.all()
    ]


@router.get("/success/", response_model=PaymentSuccessSchema, status_code=status.HTTP_200_OK)
def payment_success(
        payment_id: int,
        background_tasks: BackgroundTasks,
        db: Session = Depends(get_db),
):
    try:
        payment = db.query(PaymentModel).filter_by(id=payment_id).first()
        if not payment:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND
            )
        payment.status = "successful"
        session = stripe.checkout.Session.retrieve(payment.external_payment_id)
        order = db.query(OrderModel).filter_by(id=payment.order_id).first()
        order.status = "paid"
        user = db.query(UserModel).filter_by(id=payment.user_id).first()
        movie_ids = [order_item.movie_id for order_item in order.order_items]
        purchases = [
            Purchases(
                user_id=user.id,
                movie_id=movie_id
            )
            for movie_id in movie_ids
        ]
        db.add_all(purchases)
        db.delete(user.cart)
        db.commit()
        background_tasks.add_task(
            send_email,
            user.email,
            f"Your payment was success on {payment.amount}",
            "Thanks for buying movies!",
        )
        return {
            "message": "Payment successful",
            "amount_paid": session.amount_total / 100,
            "currency": session.currency,
        }
    except SQLAlchemyError:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@router.get("/cancel/", response_model=PaymentCancelSchema, status_code=status.HTTP_200_OK)
def payment_cancel(
        payment_id: int,
        db: Session = Depends(get_db),
):
    try:
        payment = db.query(PaymentModel).filter_by(id=payment_id).first()
        if not payment:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND
            )
        payment.status = "canceled"
        session = stripe.checkout.Session.retrieve(payment.external_payment_id)
        order = db.query(OrderModel).filter_by(id=payment.order_id).first()
        order.status = "canceled"
        db.commit()
        return {
            "message": "Payment was cancelled.You can pay the rent within 24 hours",
            "pay_here": session.url,
            "amount_paid": session.amount_total / 100,
            "currency": session.currency,
        }
    except SQLAlchemyError:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR
        )
