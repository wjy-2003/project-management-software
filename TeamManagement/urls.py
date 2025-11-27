from django.urls import path

from . import views

app_name = "TeamManagement"

urlpatterns = [
    path("", views.team_list, name="team-list"),
    path("create/", views.team_create, name="team-create"),
    path("<int:pk>/", views.team_detail, name="team-detail"),
    path("<int:pk>/update/", views.team_update, name="team-update"),
    path("<int:pk>/delete/", views.team_delete, name="team-delete"),
    path("<int:pk>/members/", views.team_member_list, name="team-member-list"),
    path("<int:pk>/members/add/", views.team_member_add, name="team-member-add"),
    path(
        "<int:pk>/members/<int:member_id>/remove/",
        views.team_member_remove,
        name="team-member-remove",
    ),
]
