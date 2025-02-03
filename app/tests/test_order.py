from datetime import datetime, timezone

from app.cart.models import CartModel, CartItemModel
from app.orders.models import OrderModel, OrderItemModel
from app.movies.models import MovieModel
from app.accounts.models import UserModel, UserGroupModel


def create_admin_user(db_session):
    """
    Creates an admin user and ensures the 'ADMIN' user group exists.
    """
    admin_group = db_session.query(UserGroupModel).filter_by(name='ADMIN').first()

    if not admin_group:
        admin_group = UserGroupModel(name='ADMIN')
        db_session.add(admin_group)
        db_session.commit()
    user = UserModel(
        email="admin@example.com",
        _hashed_password="FAfg231!@",
        group_id=3,
        group=admin_group
    )
    db_session.add(user)
    db_session.commit()
    return user


def create_user(
        db_session,
        email="user@example.com",
        password="password",
):
    """
    Creates a user and ensures the 'USER' user group exists.
    """
    admin_group = db_session.query(UserGroupModel).filter_by(name='USER').first()

    if not admin_group:
        admin_group = UserGroupModel(name='USER')
        db_session.add(admin_group)
        db_session.commit()
    user = UserModel(
        email=email,
        _hashed_password=password,
        group_id=1
    )
    db_session.add(user)
    db_session.commit()
    return user


def create_movie(
        db_session,
        name="Inception",
        year=2010,
        time=148,
        imdb=8.8,
        votes=2200000,
        price=12.99,
        description="A mind-bending thriller.",
        meta_score=74,
        gross=829895144.00,
        certification_id=2
):
    """
     Creates a movie entry in the database.
    """
    movie = MovieModel(
        name=name,
        year=year,
        time=time,
        imdb=imdb,
        votes=votes,
        price=price,
        description=description,
        meta_score=meta_score,
        gross=gross,
        certification_id=certification_id
    )
    db_session.add(movie)
    db_session.commit()
    return movie


def create_order(db_session, user_id, movie, status="canceled"):
    """
    Creates an order for a specific user and movie, and adds an order item.
    """
    order = OrderModel(
        user_id=user_id,
        status=status,
        created_at=datetime.now(timezone.utc),
        total_amount=10
    )
    db_session.add(order)
    db_session.flush()

    order_item = OrderItemModel(
        order_id=order.id,
        movie_id=movie.id,
        price_at_order=movie.price
    )
    db_session.add(order_item)
    db_session.commit()

    return order


def generate_token(user_id, jwt_manager):
    """
    Generates an access token for a user.
    """
    return jwt_manager.create_access_token({"user_id": user_id})


def test_get_orders_as_admin(client, db_session, jwt_manager):
    """
    Test for retrieving orders filtered by date.
    """
    admin = create_admin_user(db_session)
    create_user(db_session, email="NOadmin@mai.pp", password="r21FDAF")
    movie = create_movie(
        db_session,
        name="Inception",
        year=2010,
        time=148,
        imdb=8.8,
        votes=2200000,
        price=12.99,
        description="A mind-bending thriller.",
        meta_score=74,
        gross=829895144.00,
        certification_id=2
    )

    create_order(db_session, user_id=2, movie=movie, status="canceled")

    token = generate_token(admin.id, jwt_manager)
    response = client.get("/api/v1/orders/", headers={"Authorization": f"Bearer {token}"})

    assert response.status_code == 200
    assert len(response.json()) == 1
    assert response.json()[0]["movies"] == ["Inception"]
    assert response.json()[0]["status"] == "canceled"


def test_get_orders_filtered_by_date(client, db_session, jwt_manager):
    """
    Test for retrieving orders filtered by date.
    """
    admin = create_admin_user(db_session)
    create_user(db_session, "newuser@mail.com", "dsaf#!@QQ")
    movie = create_movie(
        db_session,
        name="Inception",
        year=2010,
        time=148,
        imdb=8.8,
        votes=2200000,
        price=12.99,
        description="A mind-bending thriller.",
        meta_score=74,
        gross=829895144.00,
        certification_id=2
    )

    order_date = datetime.now(timezone.utc).date()
    create_order(db_session, user_id=2, movie=movie, status="canceled")

    token = generate_token(admin.id, jwt_manager)
    response = client.get(
        f"/api/v1/orders/?order_date={order_date}",
        headers={"Authorization": f"Bearer {token}"}
    )

    assert response.status_code == 200
    assert len(response.json()) == 1


def test_get_orders_unauthorized(client):
    response = client.get("/api/v1/orders/")
    assert response.status_code == 401


def test_create_order_as_authenticated_user(client, db_session, jwt_manager):
    """
    Test for creating an order for an authorized user.
    """

    user = create_user(db_session)
    movie = create_movie(db_session)

    user_cart = user.cart
    if not user_cart:
        user.cart = CartModel(user_id=user.id)
        db_session.add(user.cart)
        db_session.commit()

    cart_item = CartItemModel(
        cart_id=user.cart.id,
        movie_id=movie.id,
        added_at=datetime.now(timezone.utc)
    )
    db_session.add(cart_item)
    db_session.commit()

    token = generate_token(user.id, jwt_manager)

    response = client.post(
        "/api/v1/orders/",
        headers={"Authorization": f"Bearer {token}"},
    )

    assert response.status_code == 201
    order_data = response.json()
    assert "date" in order_data
    assert "movies" in order_data
    assert len(order_data["movies"]) == 1
    assert order_data["status"] == "pending"


def test_create_order_without_cart(client, db_session, jwt_manager):
    """
    Test for creating an order without a cart.
    """
    user = create_user(db_session)
    token = generate_token(user.id, jwt_manager)

    response = client.post(
        "/api/v1/orders/",
        headers={"Authorization": f"Bearer {token}"},
    )

    assert response.status_code == 400
    assert response.json()["detail"] == "Bad Request"


def test_create_order_with_invalid_movie(client, db_session, jwt_manager):
    """
    Test for creating an order with incorrect movie data.
    """
    user = create_user(db_session)
    create_movie(db_session)
    invalid_movie_id = 99999
    token = generate_token(user.id, jwt_manager)

    if user.cart is None:
        user.cart = CartModel(user_id=user.id)
        db_session.add(user.cart)
        db_session.commit()

    cart_item = CartItemModel(cart_id=user.cart.id, movie_id=invalid_movie_id)

    try:
        user.cart.cart_items.append(cart_item)
        db_session.commit()
    except Exception as e:
        db_session.rollback()
        print(f"Error adding product to cart: {e}")
        raise e

    response = client.post(
        "/api/v1/orders/",
        headers={"Authorization": f"Bearer {token}"},
    )

    assert response.status_code == 400
    error_data = response.json()
    assert "detail" in error_data
    assert error_data["detail"] == "Invalid movies data"


def test_create_order_with_existing_pending_order(client, db_session, jwt_manager):
    """
    Test for creating an order with the same
    movies when there's an existing pending order.
    """
    user = create_user(db_session)
    movie1 = create_movie(db_session)
    movie2 = create_movie(db_session, name="Movie2", year=2000, time=150)

    token = generate_token(user.id, jwt_manager)

    create_order(db_session, user.id, movie1, status="pending")
    create_order(db_session, user.id, movie2, status="pending")

    response = client.post(
        "/api/v1/orders/",
        headers={"Authorization": f"Bearer {token}"},
    )

    assert response.status_code == 400
    assert response.json().get("detail") == "Bad Request"


def test_create_order_as_unauthenticated_user(client):
    """
    Test for creating an order as an unauthenticated user.
    """
    response = client.post("/api/v1/orders/")

    assert response.status_code == 401
    assert response.json()["detail"] == "Authorization header is missing"


from decimal import Decimal


def test_create_order_with_multiple_movies(client, db_session, jwt_manager):
    """
    Test for creating an order with multiple movies.
    """
    user = create_user(db_session)
    movie1 = create_movie(db_session)
    movie2 = create_movie(db_session, name="Movie2", year=2000, time=150)

    token = generate_token(user.id, jwt_manager)

    if not user.cart:
        user.cart = CartModel(user_id=user.id)
        db_session.add(user.cart)
        db_session.commit()
        db_session.refresh(user)

    user.cart.cart_items.append(CartItemModel(movie_id=movie1.id))
    user.cart.cart_items.append(CartItemModel(movie_id=movie2.id))

    db_session.commit()

    response = client.post(
        "/api/v1/orders/",
        headers={"Authorization": f"Bearer {token}"},
    )

    assert response.status_code == 201
    assert len(response.json()["movies"]) == 2
    assert movie1.name in response.json()["movies"]
    assert movie2.name in response.json()["movies"]

    total_amount = (Decimal(movie1.price) + Decimal(movie2.price)).quantize(Decimal('0.01'))

    assert Decimal(response.json()["total_amount"]).quantize(Decimal('0.01')) == total_amount
