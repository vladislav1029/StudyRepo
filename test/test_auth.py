# core/tests/test_auth.py

from django.test import TestCase
from django.urls import reverse
from django.contrib.auth.models import User
import json


class AuthAPITestCase(TestCase):
    def setUp(self):
        # Создаём пользователя для теста
        self.user = User.objects.create_user(
            username="testuser",
            email="test@example.com",
            password="strongpassword123"
        )
        self.login_data = {
            "username": "testuser",
            "password": "strongpassword123"
        }

    def test_full_auth_flow(self):
        client = self.client

        # 1. Логинимся и получаем CSRF-токен
        response = client.post(
            reverse("api-1.0.0:login_user"),  # ← Убедитесь, что имя совпадает!
            data=json.dumps(self.login_data),
            content_type="application/json"
        )
        self.assertEqual(response.status_code, 200)
        login_data = response.json()
        self.assertTrue(login_data["success"])
        self.assertIn("csrfToken", login_data)

        csrf_token = login_data["csrfToken"]

        # 2. Проверяем /me — должен быть доступен
        response = client.get(reverse("api-1.0.0:me"))
        self.assertEqual(response.status_code, 200)
        me_data = response.json()
        self.assertEqual(me_data["username"], "testuser")

        # 3. Выход — передаём CSRF-токен в заголовке
        response = client.post(
            reverse("api-1.0.0:logout_user"),
            data=json.dumps({}),
            content_type="application/json",
            HTTP_X_CSRFTOKEN=csrf_token  # ← Ключевой момент!
        )
        self.assertEqual(response.status_code, 200)
        logout_data = response.json()
        self.assertTrue(logout_data["success"])

        # 4. Проверяем, что пользователь больше не авторизован
        response = client.get(reverse("api-1.0.0:me"))
        self.assertEqual(response.status_code, 401)  # Unauthorized