from typing import Optional

from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy import ForeignKey, func, DateTime, Index
from core.database import Base
from datetime import datetime


class CartModel(Base):
    __tablename__ = "carts"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(
        ForeignKey("users.id"), nullable=True, unique=True
    )
    user: Mapped["UserModel"] = relationship(
        "UserModel", back_populates="cart"
    )

    cart_items: Mapped[list["CartItemModel"]] = relationship(
        "CartItemModel", back_populates="cart", cascade="all, delete-orphan"
    )

    def __repr__(self):
        return f"<CartModel(id={self.id}, user_id={self.user_id}>"


class CartItemModel(Base):
    __tablename__ = "cart_items"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    cart_id: Mapped[int] = mapped_column(
        ForeignKey("carts.id", ondelete="CASCADE"), nullable=False
    )
    movie_id: Mapped[Optional[int]] = mapped_column(
        ForeignKey("movies.id", ondelete="CASCADE"), nullable=False
    )
    added_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )

    cart = relationship("CartModel", back_populates="cart_items")
    movie = relationship("MovieModel", back_populates="cart_items")

    __table_args__ = (
        Index("unique_movie_constraint", "cart_id", "movie_id", unique=True),
    )

    def __repr__(self):
        return f"<CartItemModel(id={self.id}, cart_id={self.cart_id}, movie_id={self.movie_id}, added_at={self.added_at})>"


class Purchases(Base):

    __tablename__ = "purchases"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    user_id: Mapped[int]
    movie_id: Mapped[int]

    __table_args__ = (
        Index("unique_purchases_constraint", "user_id", "movie_id", unique=True),
    )
