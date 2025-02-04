from decimal import Decimal

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from fastapi.testclient import TestClient
from app.movies.models import (
    MovieModel, GenreModel, StarModel, DirectorModel, CertificationModel, MovieStatusEnum
)
from core.database import Base
from app.main import app

# Setting up the test database (SQLite in-memory)
SQLALCHEMY_DATABASE_URL = "sqlite:///:memory:"
engine = create_engine(SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False})
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

client = TestClient(app)


@pytest.fixture(scope="function")
def db_session():
    """ Creates a fresh database session for each test. """
    Base.metadata.create_all(bind=engine)
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()
        Base.metadata.drop_all(bind=engine)


@pytest.fixture(scope="function")
def genre(db_session):
    genre = GenreModel(name="Action")
    db_session.add(genre)
    db_session.commit()
    db_session.refresh(genre)
    return genre


@pytest.fixture(scope="function")
def certification(db_session):
    certification = CertificationModel(name="PG-13")
    db_session.add(certification)
    db_session.commit()
    db_session.refresh(certification)
    return certification


@pytest.fixture(scope="function")
def movie(db_session, genre, certification):
    movie = MovieModel(
        name="The Matrix",
        year=1999,
        time=136,
        imdb=8.7,
        votes=1500000,
        price=19.99,
        certification_id=certification.id
    )
    movie.genres.append(genre)
    db_session.add(movie)
    db_session.commit()
    db_session.refresh(movie)
    return movie


@pytest.fixture(scope="function")
def star(db_session):
    star = StarModel(name="Keanu Reeves")
    db_session.add(star)
    db_session.commit()
    db_session.refresh(star)
    return star


@pytest.fixture(scope="function")
def director(db_session):
    director = DirectorModel(name="Lana Wachowski")
    db_session.add(director)
    db_session.commit()
    db_session.refresh(director)
    return director


def test_create_movie(db_session):
    movie = MovieModel(
        name="The Matrix",
        year=1999,
        time=136,
        imdb=8.7,
        votes=1500000,
        price=Decimal('19.99'),
        certification_id=1
    )
    db_session.add(movie)
    db_session.commit()

    saved_movie = db_session.query(MovieModel).filter_by(name="The Matrix").first()
    assert saved_movie.price == Decimal('19.99')


def test_movie_with_multiple_genres(db_session, movie, genre):
    """ Test adding multiple genres to a movie. """
    comedy = GenreModel(name="Comedy")
    db_session.add(comedy)
    db_session.commit()

    movie.genres.append(comedy)
    db_session.commit()

    assert comedy in movie.genres
    assert len(movie.genres) == 2


def test_add_star_to_movie(db_session, movie, star):
    """ Test adding a star to a movie. """
    movie.stars.append(star)
    db_session.commit()

    assert star in movie.stars


def test_add_director_to_movie(db_session, movie, director):
    """ Test adding a director to a movie"""
    movie.directors.append(director)
    db_session.commit()

    assert director in movie.directors


def test_movie_status_enum():
    """ Test the MovieStatusEnum. """
    assert MovieStatusEnum.RELEASED == "Released"
    assert MovieStatusEnum.POST_PRODUCTION == "Post Production"
    assert MovieStatusEnum.IN_PRODUCTION == "In Production"


