from django.db import models
from django.conf import settings

class Topic(models.Model):
    name = models.CharField(max_length=100, unique=True)
    description = models.TextField(blank=True)

    def __str__(self):
        return self.name

class LabTask(models.Model):
    title = models.CharField(max_length=200)
    description = models.TextField()
    topic = models.ForeignKey(Topic, on_delete=models.CASCADE, related_name='tasks')
    file = models.FileField(upload_to='lab_files/', blank=True, null=True)
    solution_file = models.FileField(upload_to='solutions/', blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.title
