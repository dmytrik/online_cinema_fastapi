from fastapi import APIRouter, HTTPException, Query, status
from sqlalchemy.exc import IntegrityError
from fastapi.params import Depends

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
)

from core.database import get_db
from sqlalchemy.orm import Session, joinedload

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
        db: Session = Depends(get_db)
):
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
):
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
