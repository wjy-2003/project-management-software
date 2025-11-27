"""
HTTP URL routing configuration
Defines REST API endpoints
"""

from django.urls import path

from . import views

app_name = "collaboration"

urlpatterns = [
    # 前端页面
    path("", views.collaboration_home, name="home"),
    path("session/<str:session_id>/", views.session_detail_page, name="session_detail"),
    # Session management
    path("sessions/create/", views.create_session, name="create_session"),
    path("sessions/<str:session_id>/", views.get_session, name="get_session"),
    path("sessions/<str:session_id>/join/", views.join_session, name="join_session"),
    path("sessions/<str:session_id>/leave/", views.leave_session, name="leave_session"),
    # Permission management
    path(
        "sessions/<str:session_id>/permissions/",
        views.update_permission,
        name="update_permission",
    ),
    path(
        "sessions/<str:session_id>/invite/",
        views.invite_member,
        name="invite_member",
    ),
    # Members and structure
    path("sessions/<str:session_id>/members/", views.list_members, name="list_members"),
    path(
        "sessions/<str:session_id>/structure/",
        views.get_structure,
        name="get_structure",
    ),
    path(
        "sessions/<str:session_id>/save/",
        views.save_file,
        name="save_file",
    ),
    # Statistics
    path("stats/", views.session_stats, name="session_stats"),
    path("sessions/", views.list_all_sessions, name="list_all_sessions"),
]
