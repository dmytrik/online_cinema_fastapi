from pydantic import BaseModel


class CartRequestSchema(BaseModel):
    movie_id: int


class CartResponseSchema(BaseModel):
    message: str
