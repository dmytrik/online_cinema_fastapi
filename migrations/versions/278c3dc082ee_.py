"""empty message

Revision ID: 278c3dc082ee
Revises:
Create Date: 2025-01-30 18:19:57.747635

"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "278c3dc082ee"
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.create_table(
        "certifications",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("name", sa.String(), nullable=False),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("name"),
    )
    op.create_table(
        "directors",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("name", sa.String(), nullable=False),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("name"),
    )
    op.create_table(
        "genres",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("name", sa.String(), nullable=False),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("name"),
    )
    op.create_table(
        "stars",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("name", sa.String(), nullable=False),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("name"),
    )
    op.create_table(
        "user_groups",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column(
            "name",
            sa.Enum("USER", "MODERATOR", "ADMIN", name="usergroupenum"),
            nullable=False,
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("name"),
    )
    op.create_table(
        "movies",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("uuid", sa.String(), nullable=True),
        sa.Column("name", sa.String(), nullable=False),
        sa.Column("year", sa.Integer(), nullable=False),
        sa.Column("time", sa.Integer(), nullable=False),
        sa.Column("imdb", sa.Float(), nullable=False),
        sa.Column("votes", sa.Integer(), nullable=False),
        sa.Column("meta_score", sa.Float(), nullable=True),
        sa.Column("gross", sa.Float(), nullable=True),
        sa.Column("description", sa.String(), nullable=True),
        sa.Column("price", sa.DECIMAL(precision=10, scale=2), nullable=False),
        sa.Column("certification_id", sa.Integer(), nullable=False),
        sa.ForeignKeyConstraint(
            ["certification_id"],
            ["certifications.id"],
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint(
            "name", "year", "time", name="unique_movie_constraint"
        ),
    )
    op.create_table(
        "users",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("email", sa.String(length=255), nullable=False),
        sa.Column("hashed_password", sa.String(length=255), nullable=False),
        sa.Column("is_active", sa.Boolean(), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("(CURRENT_TIMESTAMP)"),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("(CURRENT_TIMESTAMP)"),
            nullable=False,
        ),
        sa.Column("group_id", sa.Integer(), nullable=False),
        sa.ForeignKeyConstraint(
            ["group_id"], ["user_groups.id"], ondelete="CASCADE"
        ),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_users_email"), "users", ["email"], unique=True)
    op.create_table(
        "activation_tokens",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("token", sa.String(length=64), nullable=False),
        sa.Column("expires_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("user_id", sa.Integer(), nullable=False),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("token"),
        sa.UniqueConstraint("user_id"),
    )
    op.create_table(
        "carts",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("user_id", sa.Integer(), nullable=True),
        sa.ForeignKeyConstraint(
            ["user_id"],
            ["users.id"],
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("user_id"),
    )
    op.create_table(
        "directors_movies",
        sa.Column("movie_id", sa.Integer(), nullable=False),
        sa.Column("director_id", sa.Integer(), nullable=False),
        sa.ForeignKeyConstraint(
            ["director_id"], ["directors.id"], ondelete="CASCADE"
        ),
        sa.ForeignKeyConstraint(
            ["movie_id"], ["movies.id"], ondelete="CASCADE"
        ),
        sa.PrimaryKeyConstraint("movie_id", "director_id"),
    )
    op.create_table(
        "movies_genres",
        sa.Column("movie_id", sa.Integer(), nullable=False),
        sa.Column("genre_id", sa.Integer(), nullable=False),
        sa.ForeignKeyConstraint(
            ["genre_id"], ["genres.id"], ondelete="CASCADE"
        ),
        sa.ForeignKeyConstraint(
            ["movie_id"], ["movies.id"], ondelete="CASCADE"
        ),
        sa.PrimaryKeyConstraint("movie_id", "genre_id"),
    )
    op.create_table(
        "orders",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("user_id", sa.Integer(), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("(CURRENT_TIMESTAMP)"),
            nullable=False,
        ),
        sa.Column(
            "status",
            sa.Enum("PENDING", "PAID", "CANCELED", name="orderstatusenum"),
            nullable=False,
        ),
        sa.Column(
            "total_amount", sa.DECIMAL(precision=10, scale=2), nullable=True
        ),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_table(
        "password_reset_tokens",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("token", sa.String(length=64), nullable=False),
        sa.Column("expires_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("user_id", sa.Integer(), nullable=False),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("token"),
        sa.UniqueConstraint("user_id"),
    )
    op.create_table(
        "refresh_tokens",
        sa.Column("token", sa.String(length=512), nullable=False),
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("expires_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("user_id", sa.Integer(), nullable=False),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("token"),
    )
    op.create_table(
        "stars_movies",
        sa.Column("movie_id", sa.Integer(), nullable=False),
        sa.Column("star_id", sa.Integer(), nullable=False),
        sa.ForeignKeyConstraint(
            ["movie_id"], ["movies.id"], ondelete="CASCADE"
        ),
        sa.ForeignKeyConstraint(["star_id"], ["stars.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("movie_id", "star_id"),
    )
    op.create_table(
        "user_profiles",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("first_name", sa.String(), nullable=True),
        sa.Column("last_name", sa.String(), nullable=True),
        sa.Column("avatar", sa.String(), nullable=True),
        sa.Column(
            "gender", sa.Enum("MAN", "WOMAN", name="genderenum"), nullable=True
        ),
        sa.Column("date_of_birth", sa.Date(), nullable=True),
        sa.Column("info", sa.Text(), nullable=True),
        sa.Column("user_id", sa.Integer(), nullable=False),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("user_id"),
        sa.UniqueConstraint("user_id"),
    )
    op.create_table(
        "cart_items",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("cart_id", sa.Integer(), nullable=False),
        sa.Column("movie_id", sa.Integer(), nullable=False),
        sa.Column(
            "added_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("(CURRENT_TIMESTAMP)"),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(["cart_id"], ["carts.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(
            ["movie_id"], ["movies.id"], ondelete="CASCADE"
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint(
            "cart_id", "movie_id", name="unique_movie_constraint"
        ),
    )
    op.create_table(
        "order_items",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("order_id", sa.Integer(), nullable=False),
        sa.Column("movie_id", sa.Integer(), nullable=False),
        sa.Column(
            "price_at_order", sa.DECIMAL(precision=10, scale=2), nullable=False
        ),
        sa.ForeignKeyConstraint(
            ["movie_id"], ["movies.id"], ondelete="CASCADE"
        ),
        sa.ForeignKeyConstraint(
            ["order_id"], ["orders.id"], ondelete="CASCADE"
        ),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_table(
        "payments",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("user_id", sa.Integer(), nullable=False),
        sa.Column("order_id", sa.Integer(), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("(CURRENT_TIMESTAMP)"),
            nullable=False,
        ),
        sa.Column(
            "status",
            sa.Enum(
                "SUCCESSFUL", "CANCELED", "REFUNDED", name="paymentstatusenum"
            ),
            nullable=False,
        ),
        sa.Column("amount", sa.DECIMAL(precision=10, scale=2), nullable=False),
        sa.Column("external_payment_id", sa.String(), nullable=True),
        sa.ForeignKeyConstraint(
            ["order_id"], ["orders.id"], ondelete="CASCADE"
        ),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_table(
        "payment_items",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("payment_id", sa.Integer(), nullable=False),
        sa.Column("order_item_id", sa.Integer(), nullable=False),
        sa.Column(
            "price_at_payment",
            sa.DECIMAL(precision=10, scale=2),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(
            ["order_item_id"], ["order_items.id"], ondelete="CASCADE"
        ),
        sa.ForeignKeyConstraint(
            ["payment_id"], ["payments.id"], ondelete="CASCADE"
        ),
        sa.PrimaryKeyConstraint("id"),
    )
    # ### end Alembic commands ###


def downgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_table("payment_items")
    op.drop_table("payments")
    op.drop_table("order_items")
    op.drop_table("cart_items")
    op.drop_table("user_profiles")
    op.drop_table("stars_movies")
    op.drop_table("refresh_tokens")
    op.drop_table("password_reset_tokens")
    op.drop_table("orders")
    op.drop_table("movies_genres")
    op.drop_table("directors_movies")
    op.drop_table("carts")
    op.drop_table("activation_tokens")
    op.drop_index(op.f("ix_users_email"), table_name="users")
    op.drop_table("users")
    op.drop_table("movies")
    op.drop_table("user_groups")
    op.drop_table("stars")
    op.drop_table("genres")
    op.drop_table("directors")
    op.drop_table("certifications")
    # ### end Alembic commands ###
