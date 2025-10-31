import factory
from django.contrib.auth import get_user_model
from django.core.files.uploadedfile import SimpleUploadedFile
from core.models import Topic, LabTask

User = get_user_model()


class UserFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = User

    username = factory.Sequence(lambda n: f'user{n}')
    email = factory.Sequence(lambda n: f'user{n}@example.com')
    password = factory.PostGenerationMethodCall('set_password', 'password123')
    is_admin = False


class AdminFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = User

    username = factory.Sequence(lambda n: f'admin{n}')
    email = factory.Sequence(lambda n: f'admin{n}@example.com')
    password = factory.PostGenerationMethodCall('set_password', 'adminpass123')
    is_admin = True


class TopicFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = Topic

    name = factory.Sequence(lambda n: f'Topic {n}')
    description = factory.Faker('paragraph')


class LabTaskFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = LabTask

    title = factory.Sequence(lambda n: f'Lab Task {n}')
    description = factory.Faker('text')
    topic = factory.SubFactory(TopicFactory)

    @factory.post_generation
    def with_file(self, create, extracted, **kwargs):
        if not create or not extracted:
            return

        self.file = SimpleUploadedFile(
            f"lab_{self.id}.py",
            b"# Test lab file content",
            content_type="text/x-python"
        )
        self.save()