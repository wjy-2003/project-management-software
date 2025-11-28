from django.contrib import admin

from .models import Document, Project, Task, TeamMember


@admin.register(TeamMember)
class TeamMemberAdmin(admin.ModelAdmin):
    list_display = ("user", "role", "join_date")
    search_fields = ("user__username", "role")


@admin.register(Project)
class ProjectAdmin(admin.ModelAdmin):
    list_display = (
        "project_number",
        "title",
        "status",
        "planned_start_date",
        "planned_end_date",
    )
    search_fields = ("project_number", "title")
    filter_horizontal = ("team_members", "documents")


@admin.register(Task)
class TaskAdmin(admin.ModelAdmin):
    list_display = (
        "title",
        "assigned_to",
        "status",
        "due_date",
        "estimated_hours",
        "consumed_hours",
        "remaining_hours",
    )
    list_filter = ("status", "due_date")
    search_fields = ("title", "description")
    readonly_fields = ("remaining_hours",)


@admin.register(Document)
class DocumentAdmin(admin.ModelAdmin):
    list_display = ("title", "upload_date")
    search_fields = ("title", "description")
