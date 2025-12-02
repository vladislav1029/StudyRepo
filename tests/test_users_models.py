import pytest
from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError
from tests.factories import UserFactory, AdminFactory

User = get_user_model()


class TestUserModel:
    """Тесты для модели User"""

    def test_user_creation(self, user_data):
        """Тест создания обычного пользователя"""
        user = User.objects.create_user(**user_data)

        assert user.username == user_data['username']
        assert user.email == user_data['email']
        assert user.check_password(user_data['password'])
        assert user.is_admin == user_data['is_admin']
        assert not user.is_superuser
        assert not user.is_staff

    def test_admin_creation(self, admin_data):
        """Тест создания администратора"""
        admin = User.objects.create_superuser(
            username=admin_data['username'],
            email=admin_data['email'],
            password=admin_data['password']
        )

        assert admin.username == admin_data['username']
        assert admin.email == admin_data['email']
        assert admin.check_password(admin_data['password'])
        assert admin.is_superuser
        assert admin.is_staff

    def test_user_is_admin_field(self):
        """Тест поля is_admin"""
        regular_user = UserFactory(is_admin=False)
        admin_user = UserFactory(is_admin=True)

        assert regular_user.is_admin is False
        assert admin_user.is_admin is True

    def test_user_string_representation(self):
        """Тест строкового представления пользователя"""
        user = UserFactory(username='testuser')
        assert str(user) == 'testuser'

    def test_user_swappable_model(self):
        """Тест заменяемой модели пользователя"""
        assert User._meta.swappable == 'AUTH_USER_MODEL'

    def test_user_email_normalization(self):
        """Тест нормализации email"""
        email = 'Test@Example.COM'
        user = UserFactory(email=email)
        assert user.email == 'Test@example.com'

    def test_user_without_username(self):
        """Тест создания пользователя без username"""
        with pytest.raises(ValueError):
            User.objects.create_user(username='', email='test@example.com', password='test123')

    @pytest.mark.django_db
    def test_user_unique_username(self):
        """Тест уникальности username"""
        UserFactory(username='uniqueuser')

        with pytest.raises(Exception):
            UserFactory(username='uniqueuser')