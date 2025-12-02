import pytest
from django.core.exceptions import ValidationError
from django.db import transaction
from core.models import Topic, LabTask
from tests.factories import TopicFactory, LabTaskFactory


class TestTopicModel:
    """Тесты для модели Topic"""

    def test_topic_creation(self, topic_data):
        """Тест создания темы"""
        topic = Topic.objects.create(**topic_data)
        assert topic.name == topic_data['name']
        assert topic.description == topic_data['description']
        assert str(topic) == topic_data['name']

    def test_topic_unique_name(self, topic_data):
        """Тест уникальности имени темы"""
        Topic.objects.create(**topic_data)

        with pytest.raises(Exception):  # django.db.IntegrityError или ValidationError
            with transaction.atomic():
                Topic.objects.create(**topic_data)

    def test_topic_blank_description(self):
        """Тест пустого описания темы"""
        topic = Topic.objects.create(name='Topic without description')
        assert topic.description == ''

    def test_topic_string_representation(self):
        """Тест строкового представления темы"""
        topic = TopicFactory(name='Mathematics')
        assert str(topic) == 'Mathematics'


class TestLabTaskModel:
    """Тесты для модели LabTask"""

    def test_lab_task_creation(self, lab_task_data, topic_data):
        """Тест создания лабораторной работы"""
        topic = Topic.objects.create(**topic_data)
        lab_task = LabTask.objects.create(
            **lab_task_data,
            topic=topic
        )

        assert lab_task.title == lab_task_data['title']
        assert lab_task.description == lab_task_data['description']
        assert lab_task.topic == topic
        assert str(lab_task) == lab_task_data['title']

    def test_lab_task_auto_timestamp(self, lab_task_data):
        """Тест автоматического добавления временной метки"""
        topic = TopicFactory()
        lab_task = LabTask.objects.create(
            **lab_task_data,
            topic=topic
        )

        assert lab_task.created_at is not None

    def test_lab_task_optional_file(self, lab_task_data):
        """Тест необязательного файла"""
        topic = TopicFactory()
        lab_task = LabTask.objects.create(
            **lab_task_data,
            topic=topic,
            file=None
        )

        assert lab_task.file is None

    def test_lab_task_foreign_key_relationship(self):
        """Тест связи с Topic"""
        topic = TopicFactory()
        lab_task = LabTaskFactory(topic=topic)

        assert lab_task.topic == topic
        assert lab_task in topic.tasks.all()

    def test_lab_task_cascade_delete(self):
        """Тест каскадного удаления"""
        topic = TopicFactory()
        lab_task = LabTaskFactory(topic=topic)

        lab_task_id = lab_task.id
        topic.delete()

        with pytest.raises(LabTask.DoesNotExist):
            LabTask.objects.get(id=lab_task_id)