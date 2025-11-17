from django.urls import path

from . import views

app_name = "GitIntegration"

urlpatterns = [
    path("graph/", views.git_graph, name="git_graph"),
    path("commit/", views.git_commit, name="git_commit"),
    path("conflicts/", views.git_conflicts, name="git_conflicts"),
    path("conflicts/api/", views.git_conflicts_api, name="git_conflicts_api"),
    path(
        "resolve-conflicts/api/",
        views.git_resolve_conflicts,
        name="git_resolve_conflicts",
    ),
    path("status/api/", views.git_status_api, name="git_status_api"),
    path("stage/api/", views.git_stage_files, name="git_stage_files"),
    path("discard/api/", views.git_discard_changes, name="git_discard_changes"),
    path("commit/api/", views.git_commit_changes, name="git_commit_changes"),
    path("commits/api/", views.git_commits_api, name="git_commits_api"),
    path("branches/", views.git_branches, name="git_branches"),
    path("switch-branch/", views.git_switch_branch, name="git_switch_branch"),
    path("create-branch/", views.git_create_branch, name="git_create_branch"),
    path("cherry-pick/", views.git_cherry_pick, name="git_cherry_pick"),
    path("reset/", views.git_reset, name="git_reset"),
    path("merge/", views.git_merge, name="git_merge"),
    path("set-path/", views.set_git_path, name="set_git_path"),
    path("get-path/", views.get_git_path, name="get_git_path"),
]
