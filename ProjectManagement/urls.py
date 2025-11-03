from django.urls import path

from . import views

app_name = "projectmanagement"

urlpatterns = [
    path("projects/", views.project_list, name="project_list"),
    path("projects/create/", views.project_create, name="project_create"),
    path(
        "projects/<str:project_number>/info/", views.project_info, name="project_info"
    ),
    path(
        "projects/<str:project_number>/edit/", views.project_edit, name="project_edit"
    ),
    path(
        "projects/<str:project_number>/cancel/",
        views.project_cancel,
        name="project_cancel",
    ),
    path(
        "projects/<str:project_number>/pause/",
        views.project_pause,
        name="project_pause",
    ),
    path(
        "projects/<str:project_number>/resume/",
        views.project_resume,
        name="project_resume",
    ),
    # 任务管理相关的URL
    path(
        "projects/<str:project_number>/tasks/create/",
        views.task_create,
        name="task_create",
    ),
    path(
        "projects/<str:project_number>/tasks/<int:task_id>/edit/",
        views.task_edit,
        name="task_edit",
    ),
    path(
        "projects/<str:project_number>/tasks/<int:task_id>/delete/",
        views.task_delete,
        name="task_delete",
    ),
    # 任务状态管理
    path(
        "projects/<str:project_number>/tasks/<int:task_id>/start/",
        views.task_start,
        name="task_start",
    ),
    path(
        "projects/<str:project_number>/tasks/<int:task_id>/suspend/",
        views.task_suspend,
        name="task_suspend",
    ),
    path(
        "projects/<str:project_number>/tasks/<int:task_id>/complete/",
        views.task_complete,
        name="task_complete",
    ),
    # 文档管理相关的URL
    path(
        "projects/<str:project_number>/documents/upload/",
        views.document_upload,
        name="document_upload",
    ),
    path(
        "projects/<str:project_number>/documents/<int:document_id>/delete/",
        views.document_delete,
        name="document_delete",
    ),
]
