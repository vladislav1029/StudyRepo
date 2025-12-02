from ninja import NinjaAPI, File
from ninja_jwt.authentication import JWTAuth
from django.http import HttpResponse
from django.core.files.uploadedfile import UploadedFile
from .models import Topic, LabTask
from typing import List, Optional
from ninja import Schema
from django.db.models import Q
from datetime import datetime

api = NinjaAPI(
    title="Labs API",
    csrf=False,
    urls_namespace="labs",
)


class TopicSchema(Schema):
    id: int
    name: str
    description: str

    # Ninja использует методы resolve_* для вычисления полей схемы из объекта ORM
    # В TopicSchema поля совпадают с ORM, resolve_* не требуются


class LabTaskSchema(Schema):
    id: int
    title: str
    description: str
    topic_id: int
    file_url: Optional[str]
    solution_file_url: Optional[str]
    created_at: str  # Pydantic будет ожидать строку

    @staticmethod
    def resolve_file_url(obj: LabTask) -> Optional[str]:
        # obj - это экземпляр LabTask
        # Вычисляем file_url
        return obj.file.url if obj.file else None

    @staticmethod
    def resolve_solution_file_url(obj: LabTask) -> Optional[str]:
        # obj - это экземпляр LabTask
        # Вычисляем solution_file_url
        return obj.solution_file.url if obj.solution_file else None

    @staticmethod
    def resolve_created_at(obj: LabTask) -> str:
        # obj - это экземпляр LabTask
        # Преобразуем datetime в строку
        # Используем isoformat() для получения стандартной строки даты-времени
        if isinstance(obj.created_at, datetime):
            return obj.created_at.isoformat()
        # Если уже строка, возвращаем как есть (на всякий случай)
        return str(obj.created_at)


class CreateLabTaskSchema(Schema):
    title: str
    description: str
    topic_id: int


# Get all topics
@api.get("/topics", response=List[TopicSchema], auth=JWTAuth())
def get_topics(request):
    return Topic.objects.all()


# Search lab tasks by topic and/or query
@api.get("/search", response=List[LabTaskSchema], auth=JWTAuth())
def search_tasks(request, q: str = None, topic_id: int = None):
    queryset = LabTask.objects.all()
    if q:
        queryset = queryset.filter(Q(title__icontains=q) | Q(description__icontains=q))
    if topic_id:
        queryset = queryset.filter(topic_id=topic_id)
    # Ninja теперь сможет использовать resolve_* методы для каждого объекта в queryset
    return queryset


# View task details
@api.get("/tasks/{task_id}", response=LabTaskSchema, auth=JWTAuth())
def get_task(request, task_id: int):
    # Оборачиваем получение объекта в try-except
    try:
        task = LabTask.objects.get(id=task_id)
    except LabTask.DoesNotExist:
        # Возвращаем 404 ошибку, если объект не найден
        # Используем api.create_response или просто raise Http404
        from django.http import Http404

        raise Http404("LabTask does not exist")
        # Альтернативно, можно использовать:
        # return api.create_response(request, {"detail": "LabTask not found"}, status=404)
        # Но raise Http404 более идиоматично для Django и Ninja его корректно обработает.
    # Ninja вызовет resolve_* методы для этого объекта
    return task


# Download file
@api.get("/tasks/{task_id}/download", auth=JWTAuth())
def download_file(request, task_id: int):
    try:
        task = LabTask.objects.get(id=task_id)
    except LabTask.DoesNotExist:
        return api.create_response(request, {"error": "File not found"}, status=404)
    if task.file:
        response = HttpResponse(
            task.file.read(), content_type="application/octet-stream"
        )
        response["Content-Disposition"] = (
            f'attachment; filename="{task.file.name.split("/")[-1]}"'
        )
        return response
    return api.create_response(request, {"error": "File not found"}, status=404)


# Download solution file
@api.get("/tasks/{task_id}/download-solution", auth=JWTAuth())
def download_solution(request, task_id: int):
    try:
        task = LabTask.objects.get(id=task_id)
    except LabTask.DoesNotExist:
        return api.create_response(
            request, {"error": "Solution file not found"}, status=404
        )
    if task.solution_file:
        response = HttpResponse(
            task.solution_file.read(), content_type="application/octet-stream"
        )
        response["Content-Disposition"] = (
            f'attachment; filename="{task.solution_file.name.split("/")[-1]}"'
        )
        return response
    return api.create_response(
        request, {"error": "Solution file not found"}, status=404
    )


# Admin: create task
@api.post("/admin/tasks", response=LabTaskSchema, auth=JWTAuth(), tags=["admin"])
def create_task(request, payload: CreateLabTaskSchema):
    if not request.auth.is_admin:
        return api.create_response(
            request, {"error": "Forbidden not admin"}, status=403
        )

    topic = Topic.objects.get(id=payload.topic_id)
    task = LabTask.objects.create(
        title=payload.title,
        description=payload.description,
        topic=topic,
    )
    # Ninja вызовет resolve_* методы для этого объекта
    return task


# Admin: update task
@api.put(
    "/admin/tasks/{task_id}", response=LabTaskSchema, auth=JWTAuth(), tags=["admin"]
)
def update_task(request, task_id: int, payload: CreateLabTaskSchema):
    if not request.auth.is_admin:
        return api.create_response(
            request, {"error": "Forbidden not admin"}, status=403
        )

    try:
        task = LabTask.objects.get(id=task_id)
    except LabTask.DoesNotExist:
        return api.create_response(request, {"error": "Task not found"}, status=404)

    topic = Topic.objects.get(
        id=payload.topic_id
    )  # Получаем Topic, может не существовать
    task.title = payload.title
    task.description = payload.description
    task.topic = topic
    task.save()
    # Ninja вызовет resolve_* методы для этого объекта
    return task


# Admin: delete task
@api.delete("/admin/tasks/{task_id}", auth=JWTAuth(), tags=["admin"])
def delete_task(request, task_id: int):
    if not request.auth.is_admin:
        return api.create_response(
            request, {"error": "Forbidden not admin"}, status=403
        )

    deleted, _ = LabTask.objects.filter(id=task_id).delete()
    if deleted == 0:
        # Задача не была найдена и удалена
        return api.create_response(request, {"error": "Task not found"}, status=404)
    return {"success": True}
