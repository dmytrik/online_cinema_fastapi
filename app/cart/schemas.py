from pydantic import BaseModel


class CartRequestSchema(BaseModel):
    movie_id: int


class CartResponseSchema(BaseModel):
    message: str


class CartMovieInfo(BaseModel):
    title: str
    price: float
    genres: str
    release_year: int

    class Config:
        from_attributes = True


class CartDetailResponseSchema(BaseModel):
    movies: list[CartMovieInfo]

    class Config:
        from_attributes = True


class AdminInfoSchema(BaseModel):
    user_id: int
    user_email: str
    movies: list[str]
