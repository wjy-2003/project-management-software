from django.urls import path

from . import views

app_name = "GitIntegration"

urlpatterns = [
    path("graph/", views.git_graph, name="git_graph"),
    path("commits/api/", views.git_commits_api, name="git_commits_api"),
]
