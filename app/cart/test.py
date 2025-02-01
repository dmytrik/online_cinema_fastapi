# import pytest
# from fastapi import status
# from fastapi.testclient import TestClient
# from sqlalchemy import create_engine
# from sqlalchemy.orm import sessionmaker, Session
# from app.main import app
# from app.accounts.models import UserModel, UserGroupModel
# from core.database import Base
#
# SQLALCHEMY_DATABASE_URL = "sqlite:///:memory:"
# engine = create_engine(SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False})
# TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
#
#
# client = TestClient(app)
#
#
# @pytest.fixture(scope="function")
# def db_session():
#     Base.metadata.create_all(bind=engine)
#
#     db = TestingSessionLocal()
#     try:
#         yield db
#     finally:
#         db.close()
#         Base.metadata.drop_all(bind=engine)
#
#
# @pytest.fixture(scope="function")
# def auth_headers(db_session: Session):
#     user_group = UserGroupModel(name="user")
#     db_session.add(user_group)
#     db_session.commit()
#
#     payload = {
#         "email": "test@example.com",
#         "password": "Password123!",
#     }
#
#     user = UserModel(
#         email="test@example.com",
#         password="Password123!",
#         group_id=user_group.id,
#         is_active=True
#     )
#     db_session.add(user)
#     db_session.commit()
#
#     response = client.post("/api/v1/accounts/login/", json=payload)
#     assert response.status_code == 200
#
#     access_token = response.json()["access_token"]
#     return {"Authorization": f"Bearer {access_token}"}
#
#
# def test_create_or_update_cart(auth_headers):
#     response = client.post("/api/v1/carts/", json={"movie_id": 1}, headers=auth_headers)
#     assert response.status_code == status.HTTP_200_OK
#     assert "added in cart successfully" in response.json()["message"]
#
#
# def test_get_cart(auth_headers):
#     response = client.get("/api/v1/carts/", headers=auth_headers)
#     assert response.status_code == status.HTTP_200_OK
#     assert isinstance(response.json()["movies"], list)
#
#
# def test_remove_movie_from_cart(auth_headers):
#     response = client.delete("/api/v1/carts/", json={"movie_id": 1}, headers=auth_headers)
#     assert response.status_code == status.HTTP_200_OK
#     assert "was deleted from cart" in response.json()["message"]
#
#
# def test_remove_cart(auth_headers):
#     client.post("/api/v1/carts/", json={"movie_id": 2}, headers=auth_headers)
#
#     response = client.get("/api/v1/carts/", headers=auth_headers)
#     assert response.status_code == status.HTTP_200_OK
#     cart_id = response.json().get("id")
#
#     response = client.delete(f"/api/v1/carts/{cart_id}/", headers=auth_headers)
#     assert response.status_code == status.HTTP_204_NO_CONTENT
