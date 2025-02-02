import enum
from datetime import datetime
from typing import Optional

from sqlalchemy import ForeignKey, DateTime, func, Enum, DECIMAL
from sqlalchemy.orm import Mapped, mapped_column, relationship

from core.database import Base


class PaymentStatusEnum(str, enum.Enum):
    PENDING = "pending"
    SUCCESSFUL = "successful"
    CANCELED = "canceled"
    REFUNDED = "refunded"


class PaymentModel(Base):
    __tablename__ = "payments"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"), nullable=False
    )
    order_id: Mapped[int] = mapped_column(
        ForeignKey("orders.id", ondelete="CASCADE"), nullable=False
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    status: Mapped[PaymentStatusEnum] = mapped_column(
        Enum(PaymentStatusEnum),
        default=PaymentStatusEnum.PENDING,
        nullable=False,
    )
    amount: Mapped[float] = mapped_column(DECIMAL(10, 2), nullable=False)
    external_payment_id: Mapped[Optional[str]]

    order: Mapped["OrderModel"] = relationship(
        "OrderModel", back_populates="payments"
    )
    user: Mapped["UserModel"] = relationship(
        "UserModel", back_populates="payments"
    )

    payment_items: Mapped[list["PaymentItemModel"]] = relationship(
        "PaymentItemModel", back_populates="payment"
    )

    def __repr__(self):
        return (
            f"<PaymentModel(id={self.id}, user_id={self.user_id}, order_id={self.order_id}, "
            f"created_at={self.created_at}, status={self.status}, amount={self.amount}, "
            f"external_payment_id={self.external_payment_id})>"
        )


class PaymentItemModel(Base):
    __tablename__ = "payment_items"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    payment_id: Mapped[int] = mapped_column(
        ForeignKey("payments.id", ondelete="CASCADE"), nullable=False
    )
    order_item_id: Mapped[int] = mapped_column(
        ForeignKey("order_items.id", ondelete="CASCADE"), nullable=False
    )

    price_at_payment: Mapped[float] = mapped_column(
        DECIMAL(10, 2), nullable=False
    )

    order_item: Mapped["OrderItemModel"] = relationship(
        "OrderItemModel", back_populates="payment_items"
    )
    payment: Mapped["PaymentModel"] = relationship(
        "PaymentModel", back_populates="payment_items"
    )

    def __repr__(self):
        return (
            f"<PaymentItemModel(id={self.id}, payment_id={self.payment_id}, "
            f"order_item_id={self.order_item_id}, price_at_payment={self.price_at_payment})>"
        )
