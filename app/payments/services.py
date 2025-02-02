import stripe
from sqlalchemy.orm import Session
from fastapi.params import Depends

from app.orders.models import OrderModel
from app.payments.models import PaymentModel, PaymentItemModel
from core.database import get_db
from core.config import settings


stripe.api_key = settings.STRIPE_SECRET_KEY


def create_stripe_session(
        order: OrderModel,
        user_id: int,
        db: Session = Depends(get_db)
):

    money_to_pay = order.total_amount

    payment = PaymentModel(
        user_id=user_id,
        order_id=order.id,
        amount=order.total_amount
    )
    db.add(payment)
    db.flush()
    db.refresh(payment)

    product_name = " ".join(
        [
            order_item.movie.name for order_item in order.order_items
        ]
    )

    session = stripe.checkout.Session.create(
        payment_method_types=["card"],
        line_items=[
            {
                "price_data": {
                    "currency": "usd",
                    "product_data": {
                        "name": product_name,
                    },
                    "unit_amount": int(money_to_pay * 100),
                },
                "quantity": 1,
            }
        ],
        mode="payment",
        success_url=f"http://localhost:8000/api/v1/payments/success/?payment_id={payment.id}",
        cancel_url=f"http://localhost:8000/api/v1/payments/cancel/?payment_id={payment.id}"
    )

    payment.external_payment_id = session.id

    payment_items = [
        PaymentItemModel(
            payment_id=payment.id,
            order_item_id=order_item.id,
            price_at_payment=order_item.price_at_order
        )
        for order_item in order.order_items
    ]

    db.add_all(payment_items)
    db.commit()

    return session.url
