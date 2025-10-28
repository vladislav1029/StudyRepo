from django.contrib import admin
from .models import Topic, LabTask


@admin.register(Topic)
class TopicAdmin(admin.ModelAdmin):
    list_display = ('name', 'description')
    search_fields = ('name',)


@admin.register(LabTask)
class LabTaskAdmin(admin.ModelAdmin):
    list_display = ('title', 'topic', 'created_at')
    list_editable = ('topic',)
    search_fields = ('title', 'description')
    list_filter = ('topic', 'created_at')
