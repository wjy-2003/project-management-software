import json
import os

from django.http import JsonResponse
from django.shortcuts import render
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods

from .src.git_graph_builder import get_repo_commits
from .src.git_operations import GitOperations


def git_graph(request):
    """Render the git graph visualization page"""
    return render(request, "GitIntegration/git_graph.html")


def git_commits_api(request):
    """API endpoint to get commit data as JSON"""
    # Get the repository path - use the current git repository
    repo_path = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

    # Get query parameters
    max_commits = int(request.GET.get("max_commits", 100))

    # Extract commit data
    data = get_repo_commits(repo_path, max_commits)

    return JsonResponse(data)


@csrf_exempt
@require_http_methods(["POST"])
def git_switch_branch(request):
    """API endpoint to switch to a different branch"""
    try:
        data = json.loads(request.body)
        branch_name = data.get("branch_name")

        if not branch_name:
            return JsonResponse(
                {"success": False, "message": "Branch name is required"}, status=400
            )

        repo_path = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        git_ops = GitOperations(repo_path)
        result = git_ops.switch_branch(branch_name)

        return JsonResponse(result)

    except json.JSONDecodeError:
        return JsonResponse(
            {"success": False, "message": "Invalid JSON data"}, status=400
        )
    except Exception as e:
        return JsonResponse({"success": False, "message": str(e)}, status=500)


@csrf_exempt
@require_http_methods(["POST"])
def git_cherry_pick(request):
    """API endpoint to cherry-pick a commit"""
    try:
        data = json.loads(request.body)
        commit_sha = data.get("commit_sha")
        target_branch = data.get("target_branch")

        if not commit_sha:
            return JsonResponse(
                {"success": False, "message": "Commit SHA is required"}, status=400
            )

        repo_path = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        git_ops = GitOperations(repo_path)
        result = git_ops.cherry_pick(commit_sha, target_branch)

        return JsonResponse(result)

    except json.JSONDecodeError:
        return JsonResponse(
            {"success": False, "message": "Invalid JSON data"}, status=400
        )
    except Exception as e:
        return JsonResponse({"success": False, "message": str(e)}, status=500)


@csrf_exempt
@require_http_methods(["POST"])
def git_reset(request):
    """API endpoint to reset branch to a specific commit"""
    try:
        data = json.loads(request.body)
        commit_sha = data.get("commit_sha")
        mode = data.get("mode", "mixed")

        if not commit_sha:
            return JsonResponse(
                {"success": False, "message": "Commit SHA is required"}, status=400
            )

        repo_path = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        git_ops = GitOperations(repo_path)
        result = git_ops.reset_commits(commit_sha, mode)

        return JsonResponse(result)

    except json.JSONDecodeError:
        return JsonResponse(
            {"success": False, "message": "Invalid JSON data"}, status=400
        )
    except Exception as e:
        return JsonResponse({"success": False, "message": str(e)}, status=500)


@csrf_exempt
@require_http_methods(["POST"])
def git_merge(request):
    """API endpoint to merge branches"""
    try:
        data = json.loads(request.body)
        source_branch = data.get("source_branch")
        target_branch = data.get("target_branch")

        if not source_branch:
            return JsonResponse(
                {"success": False, "message": "Source branch is required"}, status=400
            )

        repo_path = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        git_ops = GitOperations(repo_path)
        result = git_ops.merge_branches(source_branch, target_branch)

        return JsonResponse(result)

    except json.JSONDecodeError:
        return JsonResponse(
            {"success": False, "message": "Invalid JSON data"}, status=400
        )
    except Exception as e:
        return JsonResponse({"success": False, "message": str(e)}, status=500)


@require_http_methods(["GET"])
def git_branches(request):
    """API endpoint to get all branches"""
    try:
        repo_path = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        git_ops = GitOperations(repo_path)
        branches = git_ops.get_branches()

        return JsonResponse({"success": True, "branches": branches})

    except Exception as e:
        return JsonResponse({"success": False, "message": str(e)}, status=500)
