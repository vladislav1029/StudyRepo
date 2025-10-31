import pytest
from django.conf import settings
from ninja.testing import TestClient
from ninja_jwt.tokens import RefreshToken

@pytest.fixture
def user_data():
    return {
        'username': 'testuser',
        'email': 'test@example.com',
        'password': 'testpass123',
        'is_admin': False
    }

@pytest.fixture
def admin_data():
    return {
        'username': 'admin',
        'email': 'admin@example.com',
        'password': 'adminpass123',
        'is_admin': True
    }

@pytest.fixture
def topic_data():
    return {
        'name': 'Test Topic',
        'description': 'Test topic description'
    }

@pytest.fixture
def lab_task_data():
    return {
        'title': 'Test Lab Task',
        'description': 'Test lab task description'
    }

@pytest.fixture
def api_client():
    """Фикстура для API клиента"""
    from core.api import api as core_api
    return TestClient(core_api)

@pytest.fixture
def auth_api_client():
    """Фикстура для Auth API клиента"""
    from users.api import api as users_api
    return TestClient(users_api)

@pytest.fixture
def access_token(authenticated_user):
    """Фикстура для создания access token"""
    refresh = RefreshToken.for_user(authenticated_user)
    return str(refresh.access_token)

@pytest.fixture
def authenticated_user():
    """Фикстура для аутентифицированного пользователя"""
    from tests.factories import UserFactory
    user = UserFactory()
    user.is_admin = False
    user.save()
    return user

@pytest.fixture
def authenticated_admin():
    """Фикстура для аутентифицированного администратора"""
    from tests.factories import AdminFactory
    admin = AdminFactory()
    admin.is_admin = True
    admin.save()
    return admin