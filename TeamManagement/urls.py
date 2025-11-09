from django.urls import path
from . import views

app_name = "team_management"

urlpatterns = [
    path("teams/", views.TeamListView.as_view(), name="team-list"),
    path("teams/create/", views.TeamCreateView.as_view(), name="team-create"),
    path("teams/<int:pk>/", views.TeamDetailView.as_view(), name="team-detail"),
    path("teams/<int:pk>/update/", views.TeamUpdateView.as_view(), name="team-update"),
    path("teams/<int:pk>/delete/", views.TeamDeleteView.as_view(), name="team-delete"),
    path("teams/<int:pk>/members/", views.TeamMemberListView.as_view(), name="team-member-list"),
    path("teams/<int:pk>/members/add/", views.TeamMemberCreateView.as_view(), name="team-member-add"),
    path(
        "teams/<int:pk>/members/<int:member_id>/remove/",
        views.TeamMemberDeleteView.as_view(),
        name="team-member-remove",
    ),
]