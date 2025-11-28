import json

from django.http import JsonResponse
from django.shortcuts import render
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods

from .src.git_graph_builder import get_repo_commits
from .src.git_operations import GitOperations
from .src.git_status import GitStatus
from .src.security import (GitPathValidationError,
                           get_default_git_repository_path, log_git_operation,
                           sanitize_path_string, validate_git_repository_path)


def git_graph(request):
    """Render the git graph visualization page"""
    # Get git path from query parameter or session
    git_path = request.GET.get("git_path") or request.session.get("git_path", None)

    context = {
        "current_git_path": git_path,
    }

    return render(request, "GitIntegration/git_graph.html", context)


def git_commit(request):
    """Render the git commit interface page"""
    return render(request, "GitIntegration/git_commit.html")


def git_status_api(request):
    """API endpoint to get git status information"""
    try:
        git_path = get_git_repository_path(request)
        git_status = GitStatus(git_path)
        status_data = git_status.get_status()

        return JsonResponse({"success": True, "status": status_data})

    except Exception as e:
        return JsonResponse({"success": False, "message": str(e)}, status=500)


@csrf_exempt
@require_http_methods(["POST"])
def git_stage_files(request):
    """API endpoint to stage or unstage files"""
    try:
        data = json.loads(request.body)
        file_paths = data.get("files", [])
        stage = data.get("stage", True)  # True for stage, False for unstage

        if not file_paths:
            return JsonResponse(
                {"success": False, "message": "No files specified"}, status=400
            )

        git_path = get_git_repository_path(request)
        git_status = GitStatus(git_path)

        if stage:
            result = git_status.stage_files(file_paths)
        else:
            result = git_status.unstage_files(file_paths)

        return JsonResponse(result)

    except json.JSONDecodeError:
        return JsonResponse(
            {"success": False, "message": "Invalid JSON data"}, status=400
        )
    except Exception as e:
        return JsonResponse({"success": False, "message": str(e)}, status=500)


@csrf_exempt
@require_http_methods(["POST"])
def git_commit_changes(request):
    """API endpoint to commit staged changes"""
    try:
        data = json.loads(request.body)
        message = data.get("message", "")

        if not message.strip():
            return JsonResponse(
                {"success": False, "message": "Commit message is required"}, status=400
            )

        git_path = get_git_repository_path(request)
        git_status = GitStatus(git_path)
        result = git_status.commit(message.strip())

        return JsonResponse(result)

    except json.JSONDecodeError:
        return JsonResponse(
            {"success": False, "message": "Invalid JSON data"}, status=400
        )
    except Exception as e:
        return JsonResponse({"success": False, "message": str(e)}, status=500)


@csrf_exempt
@require_http_methods(["POST"])
def git_discard_changes(request):
    """API endpoint to discard changes to files with safety confirmations"""
    user = (
        getattr(request.user, "username", "anonymous")
        if hasattr(request, "user")
        else "anonymous"
    )

    try:
        data = json.loads(request.body)
        file_paths = data.get("files", [])
        force_delete = data.get("force_delete", False)
        create_backup = data.get("create_backup", True)

        if not file_paths:
            return JsonResponse(
                {"success": False, "message": "No files specified"}, status=400
            )

        # Log the discard operation attempt
        log_git_operation(
            "git_discard_changes", str(file_paths), user=user, success=False
        )

        git_path = get_git_repository_path(request)
        git_status = GitStatus(git_path)
        result = git_status.discard_changes(
            file_paths, force_delete=force_delete, create_backup=create_backup
        )

        # Log success if operation succeeded
        if result.get("success"):
            log_git_operation(
                "git_discard_changes", str(file_paths), user=user, success=True
            )

        return JsonResponse(result)

    except json.JSONDecodeError:
        log_git_operation(
            "git_discard_changes", "invalid_json", user=user, success=False
        )
        return JsonResponse(
            {"success": False, "message": "Invalid JSON data"}, status=400
        )
    except Exception as e:
        log_git_operation("git_discard_changes", "error", user=user, success=False)
        return JsonResponse({"success": False, "message": str(e)}, status=500)


def git_conflicts(request):
    """Render the git conflict resolution page"""
    return render(request, "GitIntegration/git_conflicts.html")


def git_conflicts_api(request):
    """API endpoint to get current merge conflicts"""
    try:
        git_path = get_git_repository_path(request)
        git_status = GitStatus(git_path)
        conflicts = git_status.get_conflicts()

        return JsonResponse({"success": True, "conflicts": conflicts})

    except Exception as e:
        return JsonResponse({"success": False, "message": str(e)}, status=500)


@csrf_exempt
@require_http_methods(["POST"])
def git_resolve_conflicts(request):
    """API endpoint to resolve merge conflicts"""
    try:
        data = json.loads(request.body)
        resolutions = data.get("resolutions", [])

        if not resolutions:
            return JsonResponse(
                {"success": False, "message": "No resolutions provided"}, status=400
            )

        git_path = get_git_repository_path(request)
        git_status = GitStatus(git_path)
        result = git_status.resolve_conflicts(resolutions)

        # After resolving, try to continue the merge
        if result["success"]:
            action = data.get("action")
            if action == "continue_merge":
                continue_result = git_status.continue_merge()
                if not continue_result["success"]:
                    result["message"] += " " + continue_result["message"]
                else:
                    result["merge_completed"] = True
            elif action == "abort_merge":
                abort_result = git_status.abort_merge()
                if not abort_result["success"]:
                    result["message"] += " " + abort_result["message"]
                else:
                    result["merge_aborted"] = True

        return JsonResponse(result)

    except json.JSONDecodeError:
        return JsonResponse(
            {"success": False, "message": "Invalid JSON data"}, status=400
        )
    except Exception as e:
        return JsonResponse({"success": False, "message": str(e)}, status=500)


def git_commits_api(request):
    """API endpoint to get commit data as JSON"""
    # Get validated git path
    git_path = get_git_repository_path(request)

    # Get query parameters
    max_commits = int(request.GET.get("max_commits", 100))

    # Extract commit data
    data = get_repo_commits(str(git_path), max_commits)

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

        git_path = get_git_repository_path(request)
        git_ops = GitOperations(git_path)
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

        git_path = get_git_repository_path(request)
        git_ops = GitOperations(git_path)
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

        git_path = get_git_repository_path(request)
        git_ops = GitOperations(git_path)
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

        git_path = get_git_repository_path(request)
        git_ops = GitOperations(git_path)
        result = git_ops.merge_branches(source_branch, target_branch)

        return JsonResponse(result)

    except json.JSONDecodeError:
        return JsonResponse(
            {"success": False, "message": "Invalid JSON data"}, status=400
        )
    except Exception as e:
        return JsonResponse({"success": False, "message": str(e)}, status=500)


@csrf_exempt
@require_http_methods(["POST"])
def git_create_branch(request):
    """API endpoint to create a new branch"""
    try:
        data = json.loads(request.body)
        branch_name = data.get("branch_name")
        start_point = data.get("start_point")
        switch_to_branch = data.get("switch", False)

        if not branch_name:
            return JsonResponse(
                {"success": False, "message": "Branch name is required"}, status=400
            )

        git_path = get_git_repository_path(request)
        git_ops = GitOperations(git_path)

        if switch_to_branch:
            result = git_ops.switch_and_create_branch(branch_name, start_point)
        else:
            result = git_ops.create_branch(branch_name, start_point)

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
        git_path = get_git_repository_path(request)
        git_ops = GitOperations(git_path)
        branches = git_ops.get_branches()

        return JsonResponse({"success": True, "branches": branches})

    except Exception as e:
        return JsonResponse({"success": False, "message": str(e)}, status=500)


@csrf_exempt
@require_http_methods(["POST"])
def set_git_path(request):
    """API endpoint to set the git repository path with security validation"""
    user = (
        getattr(request.user, "username", "anonymous")
        if hasattr(request, "user")
        else "anonymous"
    )

    try:
        # Parse JSON data
        try:
            data = json.loads(request.body)
        except json.JSONDecodeError:
            log_git_operation("set_git_path", "invalid_json", user=user, success=False)
            return JsonResponse(
                {"success": False, "message": "Invalid JSON data"}, status=400
            )

        # Get and sanitize the path
        raw_path = data.get("git_path", "").strip()
        if not raw_path:
            return JsonResponse(
                {"success": False, "message": "Git path is required"}, status=400
            )

        try:
            # Sanitize input first
            sanitized_path = sanitize_path_string(raw_path)
            # Validate the path with all security checks
            validated_path = validate_git_repository_path(sanitized_path)
        except GitPathValidationError as e:
            log_git_operation("set_git_path", raw_path, user=user, success=False)
            return JsonResponse({"success": False, "message": str(e)}, status=400)

        # Save validated path to session
        request.session["git_path"] = str(validated_path)
        request.session.modified = True

        # Log successful operation
        log_git_operation("set_git_path", validated_path, user=user, success=True)

        return JsonResponse(
            {
                "success": True,
                "message": f"Git path set to: {validated_path}",
                "git_path": str(validated_path),
            }
        )

    except Exception:
        # Log unexpected errors
        log_git_operation("set_git_path", "unknown", user=user, success=False)
        return JsonResponse(
            {"success": False, "message": "Internal server error"}, status=500
        )


@require_http_methods(["GET"])
def get_git_path(request):
    """API endpoint to get the current git repository path"""
    try:
        git_path = get_git_repository_path(request)
        return JsonResponse({"success": True, "git_path": str(git_path)})
    except Exception as e:
        return JsonResponse({"success": False, "message": str(e)}, status=500)


def get_git_repository_path(request):
    """
    Helper function to get the current git repository path from session or default.
    Returns a validated and secure path.
    """
    # Get path from session first
    session_path = request.session.get("git_path")

    if session_path:
        try:
            # Validate the session path
            validated_path = validate_git_repository_path(session_path)
            return validated_path
        except Exception:
            # Log the validation failure and fall back to default
            log_git_operation("validate_session_path", session_path, success=False)
            # Clear invalid path from session
            del request.session["git_path"]
            request.session.modified = True

    # Return default path
    return get_default_git_repository_path()
