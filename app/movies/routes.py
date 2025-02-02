from fastapi import APIRouter, HTTPException, Query, status
from sqlalchemy.exc import IntegrityError
from fastapi.params import Depends

from app.accounts.models import (
    UserGroupModel,
    UserModel,
    UserGroupEnum,
)
from app.cart.models import Purchases
from app.movies.models import (
    MovieModel,
    GenreModel,
    StarModel,
    CertificationModel,
    DirectorModel,
)
from app.movies.schemas import (
    MovieListItemSchema,
    MovieListResponseSchema,
    MovieCreateSchema,
    MovieDetailSchema,
    MovieUpdateSchema,
)

from core.database import get_db
from sqlalchemy.orm import Session, joinedload
from core.dependencies import get_jwt_auth_manager
from security.interfaces import JWTAuthManagerInterface
from exceptions import BaseSecurityError
from security.http import get_token


router = APIRouter()


@router.get("/", response_model=MovieListResponseSchema)
def get_movie_list(
        page: int = Query(1, ge=1, description="Page number (1-based index)"),
        per_page: int = Query(10, ge=1, le=20, description="Number of items per page"),
        db: Session = Depends(get_db),
) -> MovieListResponseSchema:

    offset = (page - 1) * per_page

    query = db.query(MovieModel).order_by()

    order_by = MovieModel.default_order_by()

    if order_by:
        query = query.order_by(*order_by)

    total_items = query.count()
    movies = query.offset(offset).limit(per_page).all()

    if not movies:
        raise HTTPException(status_code=404, detail="No movies found.")

    movie_list = [
        MovieListItemSchema.model_validate(movie)
        for movie in movies
    ]

    total_pages = (total_items + per_page - 1) // per_page

    response = MovieListResponseSchema(
        movies=movie_list,
        prev_page=f"/movies/?page={page - 1}&per_page={per_page}" if page > 1 else None,
        next_page=f"/movies/?page={page + 1}&per_page={per_page}" if page < total_pages else None,
        total_pages=total_pages,
        total_items=total_items,
    )
    return response


@router.post(
    "/",
    response_model=MovieDetailSchema,
    status_code=status.HTTP_201_CREATED
)
def create_movie(
        movie_data: MovieCreateSchema,
        db: Session = Depends(get_db),
        jwt_manager: JWTAuthManagerInterface = Depends(get_jwt_auth_manager),
        token: str = Depends(get_token),
) -> MovieDetailSchema:

    try:
        payload = jwt_manager.decode_access_token(token)
        user_id = payload.get("user_id")
    except BaseSecurityError as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=str(e)
        )

    user_group_name =  (
        db.query(UserGroupModel.name)
        .join(UserModel, UserModel.group_id == UserGroupModel.id)
        .filter(UserModel.id == user_id)
        .scalar()
    )

    if user_group_name not in {UserGroupEnum.ADMIN, UserGroupEnum.MODERATOR}:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Permission denied: you must be admin or moderator."
        )

    existing_movie = db.query(MovieModel).filter(
        MovieModel.name == movie_data.name,
        MovieModel.year == movie_data.year
    ).first()


    if existing_movie:
        raise HTTPException(
            status_code=409,
            detail=f"A movie with the name '{movie_data.name}' and release date '{movie_data.year}' already exists."
        )

    try:
        genres = []
        for genre_name in movie_data.genres:
            genre = db.query(GenreModel).filter_by(name=genre_name).first()
            if not genre:
                genre = GenreModel(name=genre_name)
                db.add(genre)
                db.flush()
            genres.append(genre)

        directors = []
        for director_name in movie_data.directors:
            director = db.query(DirectorModel).filter_by(name=director_name).first()
            if not director:
                director = DirectorModel(name=director_name)
                db.add(director)
                db.flush()
            directors.append(director)

        stars = []
        for star_name in movie_data.stars:
            star = db.query(StarModel).filter_by(name=star_name).first()
            if not star:
                star = StarModel(name=star_name)
                db.add(star)
                db.flush()
            stars.append(star)

        certification = db.query(CertificationModel).filter_by(name=movie_data.certification).first()
        if not certification:
            certification = CertificationModel(name=movie_data.certification)
            db.add(certification)
            db.flush()

        movie = MovieModel(
            name=movie_data.name,
            year=movie_data.year,
            time=movie_data.time,
            imdb=movie_data.imdb,
            votes=movie_data.votes,
            meta_score=movie_data.meta_score,
            gross=movie_data.gross,
            description=movie_data.description,
            price=movie_data.price,
            certification=certification,
            genres=genres,
            directors=directors,
            stars=stars,
        )
        db.add(movie)
        db.commit()
        db.refresh(movie)

        return MovieDetailSchema.model_validate(movie)
    except IntegrityError:
        db.rollback()
        raise HTTPException(status_code=400, detail="Invalid input data.")


@router.get("/{movie_id}/", response_model=MovieDetailSchema)
def get_movie_by_id(
        movie_id: int,
        db: Session = Depends(get_db)
) -> MovieDetailSchema:
    movie = (
        db.query(MovieModel)
        .options(
            joinedload(MovieModel.certification),
            joinedload(MovieModel.genres),
            joinedload(MovieModel.directors),
            joinedload(MovieModel.stars),
        )
        .filter(MovieModel.id == movie_id)
        .first()
    )

    if not movie:
        raise HTTPException(
            status_code=404,
            detail="Movie with the given ID was not found."
        )

    return MovieDetailSchema.model_validate(movie)



@router.delete("/{movie_id}/", status_code=status.HTTP_204_NO_CONTENT)
def delete_movie(
        movie_id: int,
        db: Session = Depends(get_db),
        jwt_manager: JWTAuthManagerInterface = Depends(get_jwt_auth_manager),
        token: str = Depends(get_token),
):

    try:
        payload = jwt_manager.decode_access_token(token)
        user_id = payload.get("user_id")
    except BaseSecurityError as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=str(e)
        )

    user_group_name =  (
        db.query(UserGroupModel.name)
        .join(UserModel, UserModel.group_id == UserGroupModel.id)
        .filter(UserModel.id == user_id)
        .scalar()
    )

    if user_group_name not in {UserGroupEnum.ADMIN, UserGroupEnum.MODERATOR}:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Permission denied: you must be admin or moderator."
        )

    # purchased_movies = db.query(Purchases).filter(Purchases.user_id == user_id, Purchases.movie_id == movie_id).first()
    purchased_movie = db.query(Purchases).filter(Purchases.movie_id == movie_id).first()

    if purchased_movie:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="This movie cannot be deleted as it has been purchased."
        )

    movie = db.query(MovieModel).filter(MovieModel.id == movie_id).first()

    if not movie:
        raise HTTPException(
            status_code=404,
            detail="Movie with the given ID was not found."
        )

    db.delete(movie)
    db.commit()

    return {"detail": "Movie deleted successfully."}


@router.patch("/{movie_id}/")
def update_movie(
        movie_id: int,
        movie_data: MovieUpdateSchema,
        db: Session = Depends(get_db),
        jwt_manager: JWTAuthManagerInterface = Depends(get_jwt_auth_manager),
        token: str = Depends(get_token),
):
    try:
        payload = jwt_manager.decode_access_token(token)
        user_id = payload.get("user_id")
    except BaseSecurityError as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=str(e)
        )

    user_group_name =  (
        db.query(UserGroupModel.name)
        .join(UserModel, UserModel.group_id == UserGroupModel.id)
        .filter(UserModel.id == user_id)
        .scalar()
    )

    if user_group_name not in {UserGroupEnum.ADMIN, UserGroupEnum.MODERATOR}:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Permission denied: you must be admin or moderator."
        )

    movie = db.query(MovieModel).filter(MovieModel.id == movie_id).first()

    if not movie:
        raise HTTPException(
            status_code=404,
            detail="Movie with the given ID was not found."
        )

    for field, value in movie_data.model_dump(exclude_unset=True).items():
        setattr(movie, field, value)

    try:
        db.commit()
        db.refresh(movie)
    except IntegrityError:
        db.rollback()
        raise HTTPException(status_code=400, detail="Invalid input data.")
    else:
        return {"detail": "Movie updated successfully."}
