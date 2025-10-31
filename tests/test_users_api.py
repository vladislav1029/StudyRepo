import pytest
from django.contrib.auth import get_user_model
from ninja.testing import TestClient
from users.api import api as users_api
from tests.factories import UserFactory

User = get_user_model()


class TestUsersAPI:
    """Тесты для Users API endpoints"""

    @pytest.fixture
    def client(self):
        return TestClient(users_api)

    @pytest.fixture
    def user_data(self):
        return {
            "username": "testuser",
            "email": "test@example.com",
            "password1": "securepassword123",
            "password2": "securepassword123"
        }

    @pytest.fixture
    def existing_user(self):
        return UserFactory(username="existinguser", email="existing@example.com")

    @pytest.fixture
    def authenticated_user(self):
        return UserFactory()

    # Login API Tests
    def test_login_success(self, client, existing_user):
        """Тест успешного входа"""
        login_data = {
            "username": existing_user.username,
            "password": "password123"  # Пароль из factory
        }

        response = client.post("/login", json=login_data)

        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert "access" in data
        assert data["user"]["username"] == existing_user.username

        # Проверяем, что refresh token установлен в cookies
        assert "refresh_token" in response.cookies

    def test_login_invalid_credentials(self, client):
        """Тест входа с неверными учетными данными"""
        login_data = {
            "username": "nonexistent",
            "password": "wrongpassword"
        }

        response = client.post("/login", json=login_data)

        assert response.status_code == 401
        assert response.json()["detail"] == "Invalid credentials"

    def test_login_missing_fields(self, client):
        """Тест входа с отсутствующими полями"""
        response = client.post("/login", json={})

        assert response.status_code == 422  # Validation error

    # Register API Tests
    def test_register_success(self, client, user_data):
        """Тест успешной регистрации"""
        response = client.post("/register", json=user_data)

        assert response.status_code == 201
        data = response.json()
        assert data["success"] is True
        assert data["user"]["username"] == user_data["username"]
        assert data["user"]["email"] == user_data["email"]
        assert "access" in data

        # Проверяем, что пользователь создан в базе
        assert User.objects.filter(username=user_data["username"]).exists()

        # Проверяем cookies
        assert "refresh_token" in response.cookies

    def test_register_password_mismatch(self, client, user_data):
        """Тест регистрации с несовпадающими паролями"""
        user_data["password2"] = "differentpassword"

        response = client.post("/register", json=user_data)

        assert response.status_code == 400
        assert response.json()["detail"] == "Passwords do not match"
        assert not User.objects.filter(username=user_data["username"]).exists()

    def test_register_duplicate_username(self, client, user_data, existing_user):
        """Тест регистрации с существующим username"""
        user_data["username"] = existing_user.username

        response = client.post("/register", json=user_data)

        assert response.status_code == 400
        assert response.json()["detail"] == "Username already taken"

    def test_register_missing_fields(self, client):
        """Тест регистрации с отсутствующими полями"""
        response = client.post("/register", json={"username": "test"})

        assert response.status_code == 422  # Validation error

    # Refresh Token API Tests
    def test_refresh_token_success(self, client, existing_user):
        """Тест успешного обновления токена"""
        # Сначала логинимся чтобы получить refresh token
        login_data = {
            "username": existing_user.username,
            "password": "password123"
        }
        login_response = client.post("/login", json=login_data)
        refresh_token = login_response.cookies["refresh_token"].value

        # Используем refresh token
        client.cookies["refresh_token"] = refresh_token
        response = client.post("/refresh")

        assert response.status_code == 200
        assert "access" in response.json()

    def test_refresh_token_missing(self, client):
        """Тест обновления токена без refresh token"""
        response = client.post("/refresh")

        assert response.status_code == 401
        assert response.json()["detail"] == "Refresh token missing"

    def test_refresh_token_invalid(self, client):
        """Тест обновления токена с невалидным refresh token"""
        client.cookies["refresh_token"] = "invalid_token"
        response = client.post("/refresh")

        assert response.status_code == 401
        assert response.json()["detail"] == "Invalid refresh token"

    # Logout API Tests
    def test_logout_success(self, client, authenticated_user):
        """Тест успешного выхода"""
        client.force_authenticate(authenticated_user)

        # Устанавливаем refresh token в cookies
        client.cookies["refresh_token"] = "test_refresh_token"

        response = client.post("/logout")

        assert response.status_code == 200
        assert response.json()["success"] is True

        # Проверяем, что cookie удален
        assert "refresh_token" not in response.cookies or response.cookies["refresh_token"].value == ""

    def test_logout_unauthorized(self, client):
        """Тест выхода без авторизации"""
        response = client.post("/logout")
        assert response.status_code == 401

    # Me API Tests
    def test_get_me_authenticated(self, client, authenticated_user):
        """Тест получения информации о текущем пользователе"""
        client.force_authenticate(authenticated_user)
        response = client.get("/me")

        assert response.status_code == 200
        data = response.json()
        assert data["username"] == authenticated_user.username
        assert data["email"] == authenticated_user.email

    def test_get_me_unauthorized(self, client):
        """Тест получения информации о пользователе без авторизации"""
        response = client.get("/me")
        assert response.status_code == 401