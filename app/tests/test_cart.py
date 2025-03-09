from app.accounts.models import UserModel
from app.tests.conftest import jwt_manager


def generate_token(user_id, jwt_manager):
    """
    Generates an access token for a user.
    """
    return jwt_manager.create_access_token({"user_id": user_id})


def test_create_update_delete_cart(client, db, jwt_manager):

    user = UserModel(
        email="test@example.com",
        password="password",
        is_active=True,
        group_id=3
    )
    db.add(user)
    db.commit()

    token = generate_token(user.id, jwt_manager)
    client.post(
        "/api/v1/movies/",
        json={
          "name": "first",
          "year": 2015,
          "time": 10,
          "imdb": 1,
          "votes": 1,
          "meta_score": 1,
          "gross": 1,
          "description": "good movie",
          "price": 10,
          "certification": "aaafffcccdddmmm",
          "genres": [
            "Sci-Fi"
          ],
          "directors": [
            "first"
          ],
          "stars": [
            "second"
          ]
        },
        headers={"Authorization": f"Bearer {token}"}
    )
    response = client.post(
        "/api/v1/carts/",
        json={"movie_id": 1},
        headers={"Authorization": f"Bearer {token}"}
    )

    assert response.status_code == 200
    assert "first added in cart successfully" == response.json()["message"]

    remove_movie_response = client.post(
        "/api/v1/carts/movie-delete",
        json={"movie_id": 1},
        headers={"Authorization": f"Bearer {token}"}
    )

    assert remove_movie_response.status_code == 200
    assert "first was deteled from cart number 1 successfully" == remove_movie_response.json()["message"]

    remove_cart_response = client.delete(
        "/api/v1/carts/cart/",
        headers={"Authorization": f"Bearer {token}"}
    )

    assert remove_cart_response.status_code == 204
