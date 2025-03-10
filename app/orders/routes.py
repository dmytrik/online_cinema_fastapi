from datetime import date

from fastapi import APIRouter, status, Depends, HTTPException, responses
from sqlalchemy import func, and_
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session

from app.accounts.models import UserModel
from app.cart.models import Purchases
from app.movies.models import MovieModel
from app.orders.models import OrderModel, OrderItemModel
from app.orders.schemas import OrderCreateResponseSchema, OrderListResponseSchema
from app.payments.models import PaymentModel
from core.database import get_db
from core.dependencies import get_current_user_id
from app.payments.services import create_stripe_session


router = APIRouter()


@router.get("/", response_model=list[OrderListResponseSchema], status_code=status.HTTP_200_OK)
def get_orders(
        id_user: int = None,
        order_date: date = None,
        order_status: str = None,
        db: Session = Depends(get_db),
        user_id: int = Depends(get_current_user_id),
):
    user = db.query(UserModel).filter_by(id=user_id).first()

    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
        )

    orders = db.query(OrderModel)
    if user.group.name == "admin":
        if id_user:
            orders = orders.filter_by(user_id=id_user)
        if order_date:
            orders = orders.filter(func.DATE(OrderModel.created_at) == order_date)
        if order_status:
            orders = orders.filter_by(status=order_status)
    else:
        orders = orders.filter_by(user_id=user.id)

    return [
        {
            "date": order.created_at,
            "movies": [order_item.movie.name for order_item in order.order_items],
            "total_amount": order.total_amount,
            "status": order.status
        }
        for order in orders.all()
    ]


@router.post("/", response_model=OrderCreateResponseSchema, status_code=status.HTTP_201_CREATED)
def create_order(
        db: Session = Depends(get_db),
        user_id: int = Depends(get_current_user_id),
):
    user = db.query(UserModel).filter_by(id=user_id).first()

    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
        )

    if not user.cart:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
        )

    movies_ids = [cart_item.movie_id for cart_item in user.cart.cart_items]

    movies = db.query(MovieModel).filter(MovieModel.id.in_(movies_ids))

    if movies.count() != len(movies_ids):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid movies data"
        )

    user_orders = db.query(OrderModel).filter_by(user_id=user.id).all()

    if user_orders:
        for order in user_orders:
            order_movies_ids = [order_item.movie_id for order_item in order.order_items]
            if len(set(order_movies_ids + movies_ids)) == len(movies_ids):
                if order.status == "pending":
                    raise HTTPException(
                        status_code=status.HTTP_400_BAD_REQUEST,
                        detail="you already have order with the same movies"
                    )

    total_amount = sum(movie.price for movie in movies)

    try:
        order = OrderModel(
            user_id=user.id,
            total_amount=total_amount
        )
        db.add(order)
        db.flush()

        order_items = [
            OrderItemModel(
                order_id=order.id,
                movie_id=movie.id,
                price_at_order=movie.price,

            )
            for movie in movies
        ]

        db.add_all(order_items)
        session_url = create_stripe_session(order, user_id, db)
        db.commit()
        return {
            "date": order.created_at,
            "movies": [movie.name for movie in movies],
            "total_amount": order.total_amount,
            "status": order.status,
            "pay_here": session_url
        }
    except SQLAlchemyError:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to create order"
        )


@router.post("/refund/", status_code=status.HTTP_200_OK)
def refund_order(
        order_id: int,
        db: Session = Depends(get_db),
        user_id: int = Depends(get_current_user_id),
):
    order = db.query(OrderModel).filter_by(id=order_id).first()
    payment = db.query(PaymentModel).filter_by(order_id=order_id).first()
    if order.user_id != user_id or payment.status == "refunded":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST
        )
    try:
        order.status = "canceled"
        payment.status = "refunded"
        movie_ids = [order_item.movie_id for order_item in order.order_items]
        db.query(Purchases).filter(
            and_(Purchases.movie_id.in_(movie_ids), Purchases.user_id == user_id)
        ).delete()
        db.commit()
        return {
            "message": "your order was refunded"
        }
    except SQLAlchemyError:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR
        )
