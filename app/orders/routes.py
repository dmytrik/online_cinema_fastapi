from datetime import date

from fastapi import APIRouter, status, Depends, HTTPException
from sqlalchemy import func
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session

from app.accounts.models import UserModel
from app.movies.models import MovieModel
from app.orders.models import OrderModel, OrderItemModel
from app.orders.schemas import OrderResponseSchema
from core.database import get_db
from core.dependencies import get_jwt_auth_manager
from exceptions import BaseSecurityError
from security.http import get_token
from security.interfaces import JWTAuthManagerInterface


router = APIRouter()


@router.get("/", response_model=list[OrderResponseSchema], status_code=status.HTTP_200_OK)
def get_orders(
        id_user: int = None,
        order_date: date = None,
        order_status: str = None,
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


@router.post("/", response_model=OrderResponseSchema, status_code=status.HTTP_201_CREATED)
def create_order(
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
        db.commit()
        return {
            "date": order.created_at,
            "movies": [movie.name for movie in movies],
            "total_amount": order.total_amount,
            "status": order.status
        }
    except SQLAlchemyError:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to create order"
        )
