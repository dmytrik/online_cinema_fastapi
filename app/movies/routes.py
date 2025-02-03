from typing import Optional

from fastapi import APIRouter, HTTPException, Query, status, Response, BackgroundTasks
from sqlalchemy.exc import IntegrityError
from fastapi.params import Depends
from sqlalchemy import asc, desc

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
    FavoriteMovieModel,
    MovieLikeModel,
    MovieDislikeModel, MovieCommentModel, AnswerCommentsModel,
)
from app.movies.schemas import (
    MovieListItemSchema,
    MovieListResponseSchema,
    MovieCreateSchema,
    MovieDetailSchema,
    MovieUpdateSchema,
    MoviesRequestSchema, MovieCommentSchema, MovieCommentDeleteSchema, MovieAnswerCommentSchema,
)

from core.database import get_db
from sqlalchemy.orm import Session, joinedload
from core.dependencies import get_jwt_auth_manager
from security.interfaces import JWTAuthManagerInterface
from exceptions import BaseSecurityError
from security.http import get_token
from app.accounts.email_service import send_email


router = APIRouter()

@router.delete("/comments/")
def remove_comments(
        comment_data: MovieCommentDeleteSchema,
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

    comments = db.query(MovieCommentModel).filter_by(user_id=user_id).all()

    comments_ids = [comment.id for comment in comments]

    if comment_data.id in comments_ids:
        comment = db.query(MovieCommentModel).filter_by(id=comment_data.id).first()

        db.delete(comment)
        db.commit()
        return Response(
            status_code=status.HTTP_204_NO_CONTENT
        )

    raise HTTPException(
        status_code=status.HTTP_404_NOT_FOUND,
        detail=f"comment with id {comment_data.id} was not found."
    )


@router.delete("/answer/")
def remove_answer(
        comment_data: MovieCommentDeleteSchema,
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

    comments = db.query(AnswerCommentsModel).filter_by(user_id=user_id).all()

    comments_ids = [comment.id for comment in comments]

    if comment_data.id in comments_ids:
        comment = db.query(AnswerCommentsModel).filter_by(id=comment_data.id).first()

        db.delete(comment)
        db.commit()
        return Response(
            status_code=status.HTTP_204_NO_CONTENT
        )

    raise HTTPException(
        status_code=status.HTTP_404_NOT_FOUND,
        detail=f"comment with id {comment_data.id} was not found."
    )


@router.post("/favorite/")
def add_favorite(
        movie_data: MoviesRequestSchema,
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

    existing_movie = db.query(MovieModel).get(movie_data.id)

    if not existing_movie:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Movie with the given ID was not found."
        )

    existing_favorite = db.query(FavoriteMovieModel).filter_by(user_id=user_id, movie_id=movie_data.id).first()
    if existing_favorite:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Movie already in favorites"
        )

    favorite = FavoriteMovieModel(user_id=user_id, movie_id=movie_data.id)
    db.add(favorite)
    db.commit()
    return {"detail": "Movie added to favorites"}


@router.delete("/favorite/")
def remove_favorite(
        movie_data: MoviesRequestSchema,
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

    existing_movie = db.query(MovieModel).get(movie_data.id)

    if not existing_movie:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Movie with the given ID was not found."
        )

    favorite = db.query(FavoriteMovieModel).filter_by(user_id=user_id, movie_id=movie_data.id).first()
    if not favorite:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Movie not in favorites"
        )

    db.delete(favorite)
    db.commit()
    return {"detail": f"Movie with id: {movie_data.id} removed from favorites"}


@router.get(
    "/favorites/",
    response_model=list[MovieListItemSchema]
)
def get_favorites(
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

    movies = db.query(MovieModel).join(FavoriteMovieModel).filter(FavoriteMovieModel.user_id == user_id).all()

    return [
        MovieListItemSchema.model_validate(movie)
        for movie in movies
    ]


@router.get("/", response_model=MovieListResponseSchema)
def get_movie_list(
        year: Optional[int] = None,
        imdb: Optional[int] = None,
        sort_by: Optional[str] = "id",
        sort_order: Optional[str] = "desc",
        page: int = Query(1, ge=1, description="Page number (1-based index)"),
        per_page: int = Query(10, ge=1, le=20, description="Number of items per page"),
        db: Session = Depends(get_db),
) -> MovieListResponseSchema:

    offset = (page - 1) * per_page

    query = db.query(MovieModel).order_by()

    if year:
        query = query.filter_by(year=year)

    if imdb:
        query = query.filter_by(imdb=imdb)

    if sort_order not in ["asc", "desc"]:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid sort_order. Use 'asc' or 'desc'."
        )

    if sort_by not in ["id", "year", "imdb", "name", "price"]:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid sort_by field. Allowed values are id, year, imdb, name, price."
        )

    sort_direction = asc if sort_order == "asc" else desc
    query = query.order_by(sort_direction(getattr(MovieModel, sort_by)))

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


@router.post("/movies/like/", status_code=status.HTTP_201_CREATED)
def add_or_remove_like(
        movie_data: MoviesRequestSchema,
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

    existing_like = db.query(MovieLikeModel).filter(MovieLikeModel.user_id == user_id, MovieLikeModel.movie_id == movie_data.id).first()


    if existing_like:
        db.delete(existing_like)
        db.commit()
        return Response(
            status_code=status.HTTP_204_NO_CONTENT
        )

    like = MovieLikeModel(user_id=user_id, movie_id=movie_data.id)

    db.add(like)
    db.commit()

    existing_dislike = db.query(MovieDislikeModel).filter(MovieDislikeModel.user_id == user_id, MovieDislikeModel.movie_id == movie_data.id).first()
    if existing_dislike:
        db.delete(existing_dislike)
        db.commit()

    return {"detail": "like was created"}


@router.post("/movies/dislike/", status_code=status.HTTP_201_CREATED)
def add_or_remove_dislike(
        movie_data: MoviesRequestSchema,
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

    existing_dislike = db.query(MovieDislikeModel).filter(MovieDislikeModel.user_id == user_id, MovieDislikeModel.movie_id == movie_data.id).first()

    if existing_dislike:
        db.delete(existing_dislike)
        db.commit()
        return Response(
            status_code=status.HTTP_204_NO_CONTENT
        )

    dislike = MovieDislikeModel(user_id=user_id, movie_id=movie_data.id)

    db.add(dislike)
    db.commit()

    existing_like = db.query(MovieLikeModel).filter(MovieLikeModel.user_id == user_id, MovieLikeModel.movie_id == movie_data.id).first()
    if existing_like:
        db.delete(existing_like)
        db.commit()

    return {"detail": "dislike was created"}


@router.post("/comments/")
def add_comment(
        movie_data: MovieCommentSchema,
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

    movie = db.query(MovieModel).filter(MovieModel.id == movie_data.movie_id).first()

    if not movie:
        raise HTTPException(
            status_code=404,
            detail="Movie with the given ID was not found."
        )

    comment = MovieCommentModel(user_id=user_id, movie_id=movie_data.movie_id, text=movie_data.comment)
    db.add(comment)
    db.commit()

    return {"detail": f"Comment added with movie id: {movie_data.movie_id}"}


@router.get("/{movie_id}/comments/")
def get_comments(
        movie_id: int,
        db: Session = Depends(get_db)
):
    comments = db.query(MovieCommentModel).filter_by(movie_id=movie_id).all()

    if not comments:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No comments found."
        )

    return comments


@router.post("/answer/")
def add_answer_comment(
        answer_data: MovieAnswerCommentSchema,
        background_tasks: BackgroundTasks,
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

    answer = AnswerCommentsModel(
        comment_id=answer_data.comment_id,
        user_id=user_id,
        text=answer_data.comment
    )

    db.add(answer)
    db.commit()
    db.refresh(answer)

    comment = db.query(MovieCommentModel).filter_by(id=answer.comment_id).first()
    user_email = db.query(UserModel).filter_by(id=comment.user_id).first().email
    subject = "You have got answer on your comment"
    body = answer_data.comment

    background_tasks.add_task(
        send_email,
        user_email,
        body,
        subject,
    )

    return answer
