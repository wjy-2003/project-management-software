from django.urls import path

from . import views

app_name = "GitIntegration"

urlpatterns = [
    path("graph/", views.git_graph, name="git_graph"),
    path("commits/api/", views.git_commits_api, name="git_commits_api"),
    path("branches/", views.git_branches, name="git_branches"),
    path("switch-branch/", views.git_switch_branch, name="git_switch_branch"),
    path("cherry-pick/", views.git_cherry_pick, name="git_cherry_pick"),
    path("reset/", views.git_reset, name="git_reset"),
    path("merge/", views.git_merge, name="git_merge"),
]
