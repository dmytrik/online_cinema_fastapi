from fastapi import APIRouter, HTTPException, status, BackgroundTasks
from fastapi.params import Depends
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session, joinedload, selectinload

from app.accounts.models import UserModel
from app.cart.models import CartModel, CartItemModel, Purchases
from app.cart.schemas import (
    CartRequestSchema,
    CartResponseSchema,
    CartDetailResponseSchema,
    CartMovieInfo,
    AdminInfoSchema
)
from app.movies.models import MovieModel
from core.database import get_db
from core.dependencies import get_current_user_id
from app.accounts.email_service import send_email


router = APIRouter()


@router.post("/", response_model=CartResponseSchema)
def create_or_update_cart(
        cart_data: CartRequestSchema,
        db: Session = Depends(get_db),
        user_id: int = Depends(get_current_user_id)
):
    purchase = db.query(Purchases).filter_by(user_id=user_id, movie_id=cart_data.movie_id).first()

    if purchase:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="You have already bought this movie(")

    movie = (
        db.query(MovieModel)
        .options(
            joinedload(MovieModel.certification),
            selectinload(MovieModel.genres),
            selectinload(MovieModel.stars),
            selectinload(MovieModel.directors)
        )
        .filter_by(id=cart_data.movie_id)
        .first()
    )
    if not movie:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid input data.")

    cart = db.query(CartModel).filter_by(user_id=user_id).first()

    if not cart:
        cart = CartModel(
            user_id=user_id
        )
        db.add(cart)
        db.flush()

    if cart_data.movie_id in [cart_item.movie_id for cart_item in cart.cart_items]:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="movie already in your cart"
        )

    try:
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
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid input data"
        )


@router.delete("/", response_model=CartResponseSchema)
def remove_movie_from_cart(
        movie_data: CartRequestSchema,
        background_tasks: BackgroundTasks,
        db: Session = Depends(get_db),
        user_id: int = Depends(get_current_user_id),
):
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
        moderators = db.query(UserModel).filter_by(group_id=2).all()
        for moderator in moderators:
            background_tasks.add_task(
                send_email,
                moderator.email,
                f"{movie.name} was deleted from cart with id: {cart.id}",
                "Deleted movie from cart",
            )
    except SQLAlchemyError:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Please try again later."
        )

    return {
        "message": f"{movie.name} was deteled from cart number {cart.id} successfully"
    }


@router.delete("/cart/", status_code=status.HTTP_204_NO_CONTENT)
def remove_cart(
        db: Session = Depends(get_db),
        user_id: int = Depends(get_current_user_id),
):
    cart = db.query(CartModel).filter_by(user_id=user_id).first()

    if not cart:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Cart not found")

    db.delete(cart)
    db.commit()

    return


@router.get("/", response_model=CartDetailResponseSchema | list[AdminInfoSchema])
def get_cart(
        db: Session = Depends(get_db),
        user_id: int = Depends(get_current_user_id),
):
    user = db.query(UserModel).filter_by(id=user_id).first()
    if not user:
        raise HTTPException(
            status=status.HTTP_400_BAD_REQUEST,
            detail="user not found"
        )

    if user.group.name == "admin":
        all_carts = db.query(CartModel).all()
        carts_data = [
            {
                "user_id": cart.user_id,
                "user_email": db.query(UserModel).filter_by(id=cart.user_id).first().email,
                "movies": [
                    db.query(MovieModel).filter_by(id=cart_item.movie_id).first().name
                    for cart_item in cart.cart_items
                ]
            }
            for cart in all_carts
        ]
        return carts_data

    if not user.cart:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Cart not found")

    cart = db.query(CartModel).filter_by(id=user.cart.id).first()

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
