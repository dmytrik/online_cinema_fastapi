import enum
from datetime import datetime
from typing import Optional

from sqlalchemy import ForeignKey, DateTime, func, Enum, DECIMAL
from sqlalchemy.orm import Mapped, mapped_column, relationship

# from app import MovieModel, UserModel, PaymentModel, PaymentItemModel
from core.database import Base


class OrderStatusEnum(str, enum.Enum):
    PENDING = "pending"
    PAID = "paid"
    CANCELED = "canceled"


class OrderModel(Base):
    __tablename__ = "orders"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"), nullable=False
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    status: Mapped[OrderStatusEnum] = mapped_column(
        Enum(OrderStatusEnum), nullable=False, default=OrderStatusEnum.PENDING
    )
    total_amount: Mapped[Optional[float]] = mapped_column(DECIMAL(10, 2))

    order_items: Mapped[list["OrderItemModel"]] = relationship(
        "OrderItemModel", back_populates="order"
    )
    payments: Mapped[list["PaymentModel"]] = relationship(
        "PaymentModel", back_populates="order"
    )
    user: Mapped["UserModel"] = relationship(
        "UserModel", back_populates="orders"
    )

    def __repr__(self):
        return (
            f"<OrderModel(id={self.id}, user_id={self.user_id}, created_at={self.created_at}, "
            f"status={self.status}, total_amount={self.total_amount})>"
        )

class OrderItemModel(Base):
    __tablename__ = "order_items"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    order_id: Mapped[int] = mapped_column(
        ForeignKey("orders.id", ondelete="CASCADE"), nullable=False
    )
    movie_id: Mapped[int] = mapped_column(
        ForeignKey("movies.id", ondelete="CASCADE"), nullable=False
    )

    price_at_order: Mapped[float] = mapped_column(
        DECIMAL(10, 2), nullable=False
    )

    order: Mapped["OrderModel"] = relationship(
        "OrderModel", back_populates="order_items"
    )
    movie: Mapped["MovieModel"] = relationship(
        "MovieModel", back_populates="order_items"
    )

    payment_items: Mapped[list["PaymentItemModel"]] = relationship(
        "PaymentItemModel", back_populates="order_item"
    )

    def __repr__(self):
        return (
            f"<OrderItemModel(id={self.id}, order_id={self.order_id}, movie_id={self.movie_id}, "
            f"price_at_order={self.price_at_order})>"
        )
