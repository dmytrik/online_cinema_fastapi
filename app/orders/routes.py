from datetime import date

from fastapi import APIRouter, status, Depends, HTTPException
from sqlalchemy import cast, Date
from sqlalchemy.orm import Session

from app.accounts.models import UserModel
from app.orders.models import OrderModel
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
            status_code=order_status.HTTP_401_UNAUTHORIZED,
            detail=str(e)
        )

    user = db.query(UserModel).filter_by(id=user_id).first()

    if not user:
        raise HTTPException(
            status_code=order_status.HTTP_401_UNAUTHORIZED,
        )

    if user.group.name == "admin":
        all_orders = db.query(OrderModel)
        if id_user:
            all_orders = all_orders.filter_by(user_id=id_user)
        if order_date:
            all_orders = all_orders.filter(cast(OrderModel.created_at, Date) == cast(order_date, Date))
        if order_status:
            all_orders = all_orders.filter_by(status=order_status)

        return [
            {
                "date": order.created_at,
                "movies": [movie.name for movie in order.order_items],
                "total_amount": order.total_amount,
                "status": order.status
            }
            for order in all_orders.all()
        ]

    return [
        {
            "date": order.created_at,
            "movies": [movie.name for movie in order.order_items],
            "total_amount": order.total_amount,
            "status": order.status
        }
        for order in user.orders
    ]
