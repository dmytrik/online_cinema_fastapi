from pydantic import BaseModel, Field
from typing import Optional, List


class GenreSchema(BaseModel):
    id: int
    name: str

    model_config = {
        "from_attributes": True,
    }


class StarSchema(BaseModel):
    id: int
    name: str

    model_config = {
        "from_attributes": True,
    }


class DirectorSchema(BaseModel):
    id: int
    name: str

    model_config = {
        "from_attributes": True,
    }


class CertificationSchema(BaseModel):
    id: int
    name: str

    model_config = {
        "from_attributes": True,
    }


class ActorSchema(BaseModel):
    id: int
    name: str

    model_config = {
        "from_attributes": True,
    }


class MovieBaseSchema(BaseModel):
    name: str
    year: int
    time: int
    imdb: float
    votes: int
    meta_score: float
    gross: float
    description: str
    price: float

    model_config = {
        "from_attributes": True
    }


class MovieDetailSchema(MovieBaseSchema):
    id: int
    certification: CertificationSchema
    genres: List[GenreSchema]
    directors: List[DirectorSchema]
    stars: List[StarSchema]

    model_config = {
        "from_attributes": True,
    }


class MovieListItemSchema(BaseModel):
    id: int
    name: str
    year: int
    imdb: float
    price: float

    model_config = {
        "from_attributes": True,
    }


class MovieListResponseSchema(BaseModel):
    movies: List[MovieListItemSchema]
    prev_page: Optional[str]
    next_page: Optional[str]
    total_pages: int
    total_items: int

    model_config = {
        "from_attributes": True,
    }


class MovieCreateSchema(BaseModel):
    name: str
    year: int
    time: int
    imdb: float
    votes: int
    meta_score: float
    gross: float
    description: str
    price: float
    certification: str
    genres: List[str]
    directors: List[str]
    stars: List[str]

    model_config = {
        "from_attributes": True,
    }


class MovieUpdateSchema(BaseModel):
    name: Optional[str] = None
    year: Optional[int] = None
    time: Optional[int] = None
    imdb: Optional[float] = None
    votes: Optional[int] = None
    meta_score: Optional[float] = Field(None, ge=0)
    gross: Optional[float] = Field(None, ge=0)
    description: Optional[str] = None
    price: Optional[float] = Field(None, ge=0)

    model_config = {
        "from_attributes": True,
    }
