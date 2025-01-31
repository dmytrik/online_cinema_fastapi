from fastapi import APIRouter, HTTPException, status
from fastapi.params import Depends
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session

from app.cart.models import CartModel, CartItemModel, Purchases
from app.cart.schemas import CartRequestSchema, CartResponseSchema, CartDetailResponseSchema, CartMovieInfo
from app.movies.models import MovieModel
from core.database import get_db
from core.dependencies import get_jwt_auth_manager
from exceptions import BaseSecurityError
from security.http import get_token
from security.interfaces import JWTAuthManagerInterface

router = APIRouter()

@router.post("/", response_model=CartResponseSchema)
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
        try:
            cart_item = CartItemModel(
                cart_id=cart.id,
                movie_id=cart_data.movie_id
            )
            db.add(cart_item)
            db.commit()
        except SQLAlchemyError:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid data"
            )

        return {
            "message": f"{movie.name} added in cart successfully"
        }
    except SQLAlchemyError:
        db.rollback()
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid input data.")


@router.delete("/", response_model=CartResponseSchema)
def remove_movie_from_cart(
        movie_data: CartRequestSchema,
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

    movie = db.query(MovieModel).filter_by(id=movie_data.movie_id).first()
    if not movie:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid input data.")

    cart = db.query(CartModel).filter_by(user_id=user_id).first()

    cart_item = db.query(CartItemModel).filter_by(cart_id=cart.id, movie_id=movie_data.movie_id).first()

    if not cart or not cart_item:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid data"
        )
    try:
        db.delete(cart_item)
        db.commit()
    except SQLAlchemyError:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Please try again later."
        )

    return {
        "message": f"{movie.name} was deteled from cart number {cart.id} successfully"
    }


@router.delete("/{cart_id}/", status_code=status.HTTP_204_NO_CONTENT)
def remove_cart(
        cart_id: int,
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
    cart = db.query(CartModel).filter_by(id=cart_id).first()

    if not cart:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Cart not found")

    if cart.user_id != user_id:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token"
        )

    db.delete(cart)
    db.commit()

    return


@router.get("/{cart_id}/", response_model=CartDetailResponseSchema)
def get_cart_by_id(
        cart_id: int,
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
    cart = db.query(CartModel).filter_by(id=cart_id).first()

    if not cart:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Cart not found")

    if cart.user_id != user_id:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token"
        )

    movie_ids = [cart_item.movie_id for cart_item in cart.cart_items]

    movies = db.query(MovieModel).filter(MovieModel.id.in_(movie_ids)).all()

    movies_data = [
        CartMovieInfo(
            title=movie.name,
            price=movie.price,
            genres=" ".join(genre.name for genre in movie.genres),
            release_year=movie.year,
        ) for movie in movies
    ]

    return CartDetailResponseSchema(movies=movies_data)
