from fastapi import APIRouter, HTTPException, status
from fastapi.params import Depends
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session

from app.cart.models import CartModel, CartItemModel, Purchases
from app.cart.schemas import CartRequestSchema, CartResponseSchema
from app.movies.models import MovieModel
from core.database import get_db
from core.dependencies import get_jwt_auth_manager
from exceptions import BaseSecurityError
from security.http import get_token
from security.interfaces import JWTAuthManagerInterface

router = APIRouter()

@router.post("", response_model=CartResponseSchema)
def create_or_update_cart(
        cart_data: CartRequestSchema,
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

    try:
        purchase = db.query(Purchases).filter_by(user_id=user_id, movie_id=cart_data.movie_id).first()

        if purchase:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="You have already bought this movie(")

        movie = db.query(MovieModel).filter_by(id=cart_data.movie_id).first()
        if not movie:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid input data.")

        cart = db.query(CartModel).filter_by(user_id=user_id).first()

        if not cart:
            cart = CartModel(
                user_id=user_id
            )
            db.add(cart)
            db.flush()

        cart_item = CartItemModel(
            cart_id=cart.id,
            movie_id=cart_data.movie_id
        )
        db.add(cart_item)
        db.commit()

        return {
            "message": f"{movie.name} added in cart successfully"
        }

    except SQLAlchemyError:
        db.rollback()
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid input data.")