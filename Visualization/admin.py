# from django.contrib import admin

# Register your models here.

from django.contrib import admin
from .models import Sprint, Task

@admin.register(Sprint)
class SprintAdmin(admin.ModelAdmin):
    list_display = ('name', 'start_date', 'end_date', 'total_story_points')
    search_fields = ('name',)

@admin.register(Task)
class TaskAdmin(admin.ModelAdmin):
    list_display = ('title', 'sprint', 'status', 'story_points')
    list_filter = ('status', 'sprint')