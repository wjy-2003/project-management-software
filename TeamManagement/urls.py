from django.urls import path
from . import views

app_name = "TeamManagement"

urlpatterns = [
    path("teams/", views.team_list, name="team-list"),
    path("teams/create/", views.team_create, name="team-create"),
    path("teams/<int:pk>/", views.team_detail, name="team-detail"),
    path("teams/<int:pk>/update/", views.team_update, name="team-update"),
    path("teams/<int:pk>/delete/", views.team_delete, name="team-delete"),
    path("teams/<int:pk>/members/", views.team_member_list, name="team-member-list"),
    path("teams/<int:pk>/members/add/", views.team_member_add, name="team-member-add"),
    path(
        "teams/<int:pk>/members/<int:member_id>/remove/",
        views.team_member_remove,
        name="team-member-remove",
    ),
]