from ninja import NinjaAPI, File
from ninja_jwt.authentication import JWTAuth
from django.http import HttpResponse
from django.core.files.uploadedfile import UploadedFile
from .models import Topic, LabTask
from typing import List, Optional
from ninja import Schema
from django.db.models import Q

api = NinjaAPI(
    title="Labs API",
    csrf=False,
    urls_namespace="labs",
)


class TopicSchema(Schema):
    id: int
    name: str
    description: str


class LabTaskSchema(Schema):
    id: int
    title: str
    description: str
    topic_id: int
    file_url: Optional[str]
    solution_file_url: Optional[str]
    created_at: str

    @staticmethod
    def from_orm(task: LabTask):
        return LabTaskSchema(
            id=task.id,
            title=task.title,
            description=task.description,
            topic_id=task.topic.id,
            file_url=task.file.url if task.file else None,
            solution_file_url=task.solution_file.url if task.solution_file else None,
            created_at=str(task.created_at),
        )


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
    return queryset


# View task details
@api.get("/tasks/{task_id}", response=LabTaskSchema, auth=JWTAuth())
def get_task(request, task_id: int):
    task = LabTask.objects.get(id=task_id)
    return task


# Download file
@api.get("/tasks/{task_id}/download", auth=JWTAuth())
def download_file(request, task_id: int):
    task = LabTask.objects.get(id=task_id)
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
    task = LabTask.objects.get(id=task_id)
    if task.solution_file:
        response = HttpResponse(
            task.solution_file.read(), content_type="application/octet-stream"
        )
        response["Content-Disposition"] = (
            f'attachment; filename="{task.solution_file.name.split("/")[-1]}"'
        )
        return response
    return api.create_response(request, {"error": "Solution file not found"}, status=404)


# Admin: create task
@api.post("/admin/tasks", response=LabTaskSchema, auth=JWTAuth())
def create_task(request, payload: CreateLabTaskSchema):
    if not request.auth.is_admin:
        return api.create_response(request, {"error": "Not authorized"}, status=403)

    topic = Topic.objects.get(id=payload.topic_id)
    task = LabTask.objects.create(
        title=payload.title,
        description=payload.description,
        topic=topic,
    )
    return task


# Admin: update task
@api.put("/admin/tasks/{task_id}", response=LabTaskSchema, auth=JWTAuth())
def update_task(request, task_id: int, payload: CreateLabTaskSchema):
    if not request.auth.is_admin:
        return api.create_response(request, {"error": "Not authorized"}, status=403)

    task = LabTask.objects.get(id=task_id)
    task.title = payload.title
    task.description = payload.description
    task.topic = Topic.objects.get(id=payload.topic_id)
    task.save()
    return task


# Admin: delete task
@api.delete("/admin/tasks/{task_id}", auth=JWTAuth())
def delete_task(request, task_id: int):
    if not request.auth.is_admin:
        return api.create_response(request, {"error": "Not authorized"}, status=403)

    LabTask.objects.filter(id=task_id).delete()
    return {"success": True}
