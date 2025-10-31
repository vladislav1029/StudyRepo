import pytest
from django.core.files.uploadedfile import SimpleUploadedFile
from django.urls import reverse
from ninja.testing import TestClient
from core.api import api as core_api
from core.models import Topic, LabTask
from tests.factories import TopicFactory, LabTaskFactory, UserFactory, AdminFactory


class TestCoreAPI:
    """Тесты для Core API endpoints"""

    @pytest.fixture
    def client(self):
        return TestClient(core_api)

    @pytest.fixture
    def authenticated_user(self):
        user = UserFactory()
        user.is_admin = False
        user.save()
        return user

    @pytest.fixture
    def authenticated_admin(self):
        admin = AdminFactory()
        admin.is_admin = True
        admin.save()
        return admin

    @pytest.fixture
    def sample_topic(self):
        return TopicFactory()

    @pytest.fixture
    def sample_lab_task(self, sample_topic):
        return LabTaskFactory(topic=sample_topic)

    @pytest.fixture
    def lab_file(self):
        return SimpleUploadedFile(
            "test_lab.py",
            b"print('Hello World')",
            content_type="text/x-python"
        )

    # Topics API Tests
    def test_get_topics_unauthorized(self, client):
        """Тест получения тем без авторизации"""
        response = client.get("/topics")
        assert response.status_code == 401

    def test_get_topics_authorized(self, client, authenticated_user, sample_topic):
        """Тест получения тем с авторизацией"""
        # Создаем еще несколько тем для теста
        TopicFactory.create_batch(2)

        client.force_authenticate(authenticated_user)
        response = client.get("/topics")

        assert response.status_code == 200
        assert len(response.json()) == 3  # sample_topic + 2 новых

    def test_get_topics_empty(self, client, authenticated_user):
        """Тест получения пустого списка тем"""
        client.force_authenticate(authenticated_user)
        response = client.get("/topics")

        assert response.status_code == 200
        assert response.json() == []

    # Search API Tests
    def test_search_without_filters(self, client, authenticated_user, sample_lab_task):
        """Тест поиска без фильтров"""
        client.force_authenticate(authenticated_user)
        response = client.get("/search")

        assert response.status_code == 200
        assert len(response.json()) == 1

    def test_search_with_query(self, client, authenticated_user, sample_topic):
        """Тест поиска по текстовому запросу"""
        # Создаем задачи с разными названиями
        LabTaskFactory(title="Python Lab", description="About Python", topic=sample_topic)
        LabTaskFactory(title="Django Lab", description="About Django", topic=sample_topic)
        LabTaskFactory(title="JavaScript Lab", description="About JS", topic=sample_topic)

        client.force_authenticate(authenticated_user)
        response = client.get("/search", data={"q": "Python"})

        assert response.status_code == 200
        results = response.json()
        assert len(results) == 1
        assert "Python" in results[0]["title"]

    def test_search_with_topic_filter(self, client, authenticated_user):
        """Тест поиска по теме"""
        topic1 = TopicFactory()
        topic2 = TopicFactory()

        LabTaskFactory.create_batch(2, topic=topic1)
        LabTaskFactory.create_batch(3, topic=topic2)

        client.force_authenticate(authenticated_user)
        response = client.get("/search", data={"topic_id": topic1.id})

        assert response.status_code == 200
        assert len(response.json()) == 2

    def test_search_combined_filters(self, client, authenticated_user, sample_topic):
        """Тест поиска с комбинированными фильтрами"""
        LabTaskFactory(title="Advanced Python", description="Hard lab", topic=sample_topic)
        LabTaskFactory(title="Basic Python", description="Easy lab", topic=sample_topic)
        LabTaskFactory(title="Django Basics", description="Web framework", topic=sample_topic)

        client.force_authenticate(authenticated_user)
        response = client.get("/search", data={"q": "Python", "topic_id": sample_topic.id})

        assert response.status_code == 200
        results = response.json()
        assert len(results) == 2
        assert all("Python" in task["title"] for task in results)

    # Task Detail API Tests
    def test_get_task_detail(self, client, authenticated_user, sample_lab_task):
        """Тест получения деталей задачи"""
        client.force_authenticate(authenticated_user)
        response = client.get(f"/tasks/{sample_lab_task.id}")

        assert response.status_code == 200
        data = response.json()
        assert data["id"] == sample_lab_task.id
        assert data["title"] == sample_lab_task.title
        assert data["topic_id"] == sample_lab_task.topic.id

    def test_get_nonexistent_task(self, client, authenticated_user):
        """Тест получения несуществующей задачи"""
        client.force_authenticate(authenticated_user)
        response = client.get("/tasks/999")

        assert response.status_code == 404

    # Download API Tests
    def test_download_file_with_file(self, client, authenticated_user, sample_lab_task, lab_file):
        """Тест скачивания файла (когда файл есть)"""
        sample_lab_task.file = lab_file
        sample_lab_task.save()

        client.force_authenticate(authenticated_user)
        response = client.get(f"/tasks/{sample_lab_task.id}/download")

        assert response.status_code == 200
        assert response.headers["content-type"] == "application/octet-stream"
        assert "attachment" in response.headers["content-disposition"]

    def test_download_file_without_file(self, client, authenticated_user, sample_lab_task):
        """Тест скачивания файла (когда файла нет)"""
        client.force_authenticate(authenticated_user)
        response = client.get(f"/tasks/{sample_lab_task.id}/download")

        assert response.status_code == 404
        assert response.json()["error"] == "File not found"

    # Admin Task Creation Tests
    def test_create_task_as_admin(self, client, authenticated_admin, sample_topic):
        """Тест создания задачи администратором"""
        task_data = {
            "title": "New Lab Task",
            "description": "New task description",
            "topic_id": sample_topic.id
        }

        client.force_authenticate(authenticated_admin)
        response = client.post("/admin/tasks", json=task_data)

        assert response.status_code == 200
        data = response.json()
        assert data["title"] == task_data["title"]
        assert LabTask.objects.filter(title="New Lab Task").exists()

    def test_create_task_as_regular_user(self, client, authenticated_user, sample_topic):
        """Тест создания задачи обычным пользователем"""
        task_data = {
            "title": "New Lab Task",
            "description": "New task description",
            "topic_id": sample_topic.id
        }

        client.force_authenticate(authenticated_user)
        response = client.post("/admin/tasks", json=task_data)

        assert response.status_code == 403
        assert response.json()["error"] == "Not authorized"

    def test_create_task_invalid_topic(self, client, authenticated_admin):
        """Тест создания задачи с несуществующей темой"""
        task_data = {
            "title": "New Lab Task",
            "description": "New task description",
            "topic_id": 999
        }

        client.force_authenticate(authenticated_admin)
        response = client.post("/admin/tasks", json=task_data)

        assert response.status_code == 404

    # Admin Task Update Tests
    def test_update_task_as_admin(self, client, authenticated_admin, sample_lab_task, sample_topic):
        """Тест обновления задачи администратором"""
        update_data = {
            "title": "Updated Title",
            "description": "Updated description",
            "topic_id": sample_topic.id
        }

        client.force_authenticate(authenticated_admin)
        response = client.put(f"/admin/tasks/{sample_lab_task.id}", json=update_data)

        assert response.status_code == 200
        data = response.json()
        assert data["title"] == "Updated Title"

        sample_lab_task.refresh_from_db()
        assert sample_lab_task.title == "Updated Title"

    def test_update_task_as_regular_user(self, client, authenticated_user, sample_lab_task):
        """Тест обновления задачи обычным пользователем"""
        update_data = {
            "title": "Updated Title",
            "description": "Updated description",
            "topic_id": sample_lab_task.topic.id
        }

        client.force_authenticate(authenticated_user)
        response = client.put(f"/admin/tasks/{sample_lab_task.id}", json=update_data)

        assert response.status_code == 403

    # Admin Task Delete Tests
    def test_delete_task_as_admin(self, client, authenticated_admin, sample_lab_task):
        """Тест удаления задачи администратором"""
        task_id = sample_lab_task.id

        client.force_authenticate(authenticated_admin)
        response = client.delete(f"/admin/tasks/{task_id}")

        assert response.status_code == 200
        assert response.json()["success"] is True
        assert not LabTask.objects.filter(id=task_id).exists()

    def test_delete_task_as_regular_user(self, client, authenticated_user, sample_lab_task):
        """Тест удаления задачи обычным пользователем"""
        client.force_authenticate(authenticated_user)
        response = client.delete(f"/admin/tasks/{sample_lab_task.id}")

        assert response.status_code == 403
        assert LabTask.objects.filter(id=sample_lab_task.id).exists()