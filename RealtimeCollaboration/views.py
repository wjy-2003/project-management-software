# from django.shortcuts import render

"""
REST API views
Provide HTTP interfaces for session management
"""
import json

from django.http import JsonResponse
from django.shortcuts import render
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods

from .session_manager import session_manager


@csrf_exempt
@require_http_methods(["POST"])
def create_session(request):
    """
    Create a new collaboration session

    POST /api/collaboration/sessions/create/
    Body: multipart/form-data with optional files

    Returns: {
        "success": true,
        "session_id": "uuid",
        "message": "Session created successfully"
    }
    """
    try:
        # Check if user is authenticated - for development, allow requests with user_id
        if not request.user.is_authenticated:
            # Development fallback: use provided user_id from request
            if hasattr(request, 'POST') and request.POST.get('user_id'):
                initiator = request.POST.get('user_id')
            elif hasattr(request, 'body') and request.content_type == 'application/json':
                try:
                    body_data = json.loads(request.body)
                    initiator = body_data.get('initiator', 'user_' + str(hash(request.META.get('REMOTE_ADDR', '')) % 1000000))
                except json.JSONDecodeError:
                    initiator = 'user_' + str(hash(request.META.get('REMOTE_ADDR', '')) % 1000000)
            else:
                return JsonResponse({"success": False, "message": "请先登录"}, status=401)
        else:
            # Use the current logged-in user's ID
            initiator = str(request.user.id)

        session_id = session_manager.create_session(initiator)

        # Handle file uploads if present
        uploaded_files = request.FILES.getlist("files")
        if uploaded_files:
            import os
            import uuid as uuid_lib

            from django.conf import settings

            # Create session directory
            session_dir = os.path.join(
                settings.MEDIA_ROOT, "collaboration_sessions", session_id
            )
            os.makedirs(session_dir, exist_ok=True)

            # Save uploaded files and update structure
            session = session_manager.get_session(session_id)
            for uploaded_file in uploaded_files:
                # Save file
                file_path = os.path.join(session_dir, uploaded_file.name)
                with open(file_path, "wb+") as destination:
                    for chunk in uploaded_file.chunks():
                        destination.write(chunk)

                # Add to session structure with proper id and parent_id
                session["structure"]["files"].append(
                    {
                        "id": str(uuid_lib.uuid4()),
                        "name": uploaded_file.name,
                        "path": uploaded_file.name,
                        "parent_id": None,  # Root level file
                        "content": "",  # Will be loaded on demand
                        "type": "file",
                    }
                )

        return JsonResponse(
            {
                "success": True,
                "session_id": session_id,
                "message": "Session created successfully",
            },
            status=201,
        )

    except json.JSONDecodeError:
        return JsonResponse(
            {"success": False, "message": "Invalid JSON format"}, status=400
        )
    except Exception as e:
        return JsonResponse(
            {"success": False, "message": f"Error creating session: {str(e)}"},
            status=500,
        )


@require_http_methods(["GET"])
def get_session(request, session_id):
    """
    Retrieve session information

    GET /api/collaboration/sessions/<session_id>/

    Returns: {
        "success": true,
        "session": {
            "session_id": "uuid",
            "initiator": "user_id",
            "members": [...],
            "structure": {...}
        }
    }
    """
    try:
        session = session_manager.get_session(session_id)

        if not session:
            return JsonResponse(
                {"success": False, "message": "Session not found"}, status=404
            )

        # Get member list
        members = session_manager.get_all_members(session_id)

        return JsonResponse(
            {
                "success": True,
                "session": {
                    "session_id": session["session_id"],
                    "initiator": session["initiator"],
                    "created_at": session["created_at"],
                    "members": members,
                    "structure": session["structure"],
                },
            }
        )

    except Exception as e:
        return JsonResponse(
            {"success": False, "message": f"Error retrieving session: {str(e)}"},
            status=500,
        )


@csrf_exempt
@require_http_methods(["POST"])
def join_session(request, session_id):
    """
    Join a collaboration session

    POST /api/collaboration/sessions/<session_id>/join/
    Body: {
        "role": "editor"  # Optional: "editor" or "viewer", default "viewer"
    }

    Returns: {
        "success": true,
        "message": "Joined session successfully"
    }
    """
    try:
        # Check if user is authenticated
        if not request.user.is_authenticated:
            return JsonResponse({"success": False, "message": "请先登录"}, status=401)

        # Use the current logged-in user's ID
        member_id = str(request.user.id)

        data = json.loads(request.body) if request.body else {}
        role = data.get("role", "viewer")

        if role not in ["editor", "viewer"]:
            return JsonResponse(
                {
                    "success": False,
                    "message": 'Invalid role. Must be "editor" or "viewer"',
                },
                status=400,
            )

        if not session_manager.session_exists(session_id):
            return JsonResponse(
                {"success": False, "message": "Session not found"}, status=404
            )

        # Check if user is already a member
        session = session_manager.get_session(session_id)
        if session and member_id in session.get("members", {}):
            # User is already a member, just return success
            return JsonResponse(
                {"success": True, "message": "您已经是会话成员,可以直接打开会话"}
            )

        success = session_manager.add_member(session_id, member_id, role)

        if success:
            return JsonResponse(
                {"success": True, "message": "Joined session successfully"}
            )
        else:
            return JsonResponse(
                {"success": False, "message": "Failed to join session"}, status=500
            )

    except json.JSONDecodeError:
        return JsonResponse(
            {"success": False, "message": "Invalid JSON format"}, status=400
        )
    except Exception as e:
        return JsonResponse(
            {"success": False, "message": f"Error joining session: {str(e)}"},
            status=500,
        )


@csrf_exempt
@require_http_methods(["POST"])
def leave_session(request, session_id):
    """
    Leave a collaboration session

    POST /api/collaboration/sessions/<session_id>/leave/
    Body: {} (empty, uses current logged-in user)

    Returns: {
        "success": true,
        "message": "Left session successfully",
        "session_destroyed": false
    }
    """
    try:
        # Check if user is authenticated
        if not request.user.is_authenticated:
            return JsonResponse({"success": False, "message": "请先登录"}, status=401)

        # Use the current logged-in user's ID
        member_id = str(request.user.id)

        session_destroyed = session_manager.remove_member(session_id, member_id)

        return JsonResponse(
            {
                "success": True,
                "message": "Left session successfully",
                "session_destroyed": session_destroyed,
            }
        )

    except json.JSONDecodeError:
        return JsonResponse(
            {"success": False, "message": "Invalid JSON format"}, status=400
        )
    except Exception as e:
        return JsonResponse(
            {"success": False, "message": f"Error leaving session: {str(e)}"},
            status=500,
        )


@csrf_exempt
@require_http_methods(["POST"])
def update_permission(request, session_id):
    """
    Update a member's permission (only callable by the initiator)

    POST /api/collaboration/sessions/<session_id>/permissions/
    Body: {
        "member_id": "target_user_id",
        "role": "editor"  # "editor" or "viewer"
    }

    Returns: {
        "success": true,
        "message": "Permission updated successfully"
    }
    """
    try:
        # Check if user is authenticated
        if not request.user.is_authenticated:
            return JsonResponse({"success": False, "message": "请先登录"}, status=401)

        # Use the current logged-in user's ID as initiator
        initiator_id = str(request.user.id)

        data = json.loads(request.body)
        member_id = data.get("member_id")
        role = data.get("role")

        if not all([member_id, role]):
            return JsonResponse(
                {
                    "success": False,
                    "message": "member_id and role are required",
                },
                status=400,
            )

        if role not in ["editor", "viewer"]:
            return JsonResponse(
                {
                    "success": False,
                    "message": 'Invalid role. Must be "editor" or "viewer"',
                },
                status=400,
            )

        # Verify that the caller is the initiator
        if not session_manager.is_initiator(session_id, initiator_id):
            return JsonResponse(
                {
                    "success": False,
                    "message": "Permission denied: only initiator can change permissions",
                },
                status=403,
            )

        success = session_manager.update_member_role(session_id, member_id, role)

        if success:
            return JsonResponse(
                {"success": True, "message": "Permission updated successfully"}
            )
        else:
            return JsonResponse(
                {
                    "success": False,
                    "message": "Failed to update permission. Member may not exist.",
                },
                status=400,
            )

    except json.JSONDecodeError:
        return JsonResponse(
            {"success": False, "message": "Invalid JSON format"}, status=400
        )
    except Exception as e:
        return JsonResponse(
            {"success": False, "message": f"Error updating permission: {str(e)}"},
            status=500,
        )


@csrf_exempt
@require_http_methods(["POST"])
def invite_member(request, session_id):
    """
    Invite another user to join the session (requires initiator permission)

    POST /api/collaboration/sessions/<session_id>/invite/
    Body: {
        "user_id": "target_user_id",
        "role": "editor"  # "editor" or "viewer"
    }

    Returns: {
        "success": true,
        "message": "User invited successfully"
    }
    """
    try:
        # Check if user is authenticated
        if not request.user.is_authenticated:
            return JsonResponse({"success": False, "message": "请先登录"}, status=401)

        # Use the current logged-in user's ID as initiator
        initiator_id = str(request.user.id)

        data = json.loads(request.body)
        user_id = data.get("user_id")
        role = data.get("role", "viewer")

        if not user_id:
            return JsonResponse(
                {"success": False, "message": "user_id is required"},
                status=400,
            )

        if role not in ["editor", "viewer"]:
            return JsonResponse(
                {
                    "success": False,
                    "message": 'Invalid role. Must be "editor" or "viewer"',
                },
                status=400,
            )

        # Verify that the caller is the initiator
        if not session_manager.is_initiator(session_id, initiator_id):
            return JsonResponse(
                {
                    "success": False,
                    "message": "Permission denied: only initiator can invite members",
                },
                status=403,
            )

        # Add the user to the session
        success = session_manager.add_member(session_id, user_id, role)

        if success:
            return JsonResponse(
                {"success": True, "message": "User invited successfully"}
            )
        else:
            return JsonResponse(
                {"success": False, "message": "Failed to invite user"},
                status=500,
            )

    except json.JSONDecodeError:
        return JsonResponse(
            {"success": False, "message": "Invalid JSON format"}, status=400
        )
    except Exception as e:
        return JsonResponse(
            {"success": False, "message": f"Error inviting user: {str(e)}"},
            status=500,
        )


@require_http_methods(["GET"])
def list_members(request, session_id):
    """
    Get the list of members in a session

    GET /api/collaboration/sessions/<session_id>/members/

    Returns: {
        "success": true,
        "members": [
            {
                "member_id": "user_id",
                "role": "initiator",
                "joined_at": "2025-10-30T..."
            },
            ...
        ]
    }
    """
    try:
        if not session_manager.session_exists(session_id):
            return JsonResponse(
                {"success": False, "message": "Session not found"}, status=404
            )

        members = session_manager.get_all_members(session_id)

        return JsonResponse({"success": True, "members": members})

    except Exception as e:
        return JsonResponse(
            {"success": False, "message": f"Error retrieving members: {str(e)}"},
            status=500,
        )


@require_http_methods(["GET"])
def get_structure(request, session_id):
    """
    Retrieve folder/file structure for a session

    GET /api/collaboration/sessions/<session_id>/structure/

    Returns: {
        "success": true,
        "structure": {
            "folders": [...],
            "files": [...]
        }
    }
    """
    try:
        structure = session_manager.get_structure(session_id)

        if structure is None:
            return JsonResponse(
                {"success": False, "message": "Session not found"}, status=404
            )

        # Load file contents from disk if they exist
        import os

        from django.conf import settings

        session_dir = os.path.join(
            settings.MEDIA_ROOT, "collaboration_sessions", session_id
        )
        if os.path.exists(session_dir):
            for file_item in structure.get("files", []):
                file_path = os.path.join(session_dir, file_item["name"])
                if os.path.exists(file_path):
                    try:
                        with open(file_path, "r", encoding="utf-8") as f:
                            file_item["content"] = f.read()
                    except UnicodeDecodeError:
                        # If not UTF-8, try with other encodings or mark as binary
                        try:
                            with open(file_path, "r", encoding="gbk") as f:
                                file_item["content"] = f.read()
                        except (UnicodeDecodeError, IOError, OSError):
                            file_item["content"] = "# Binary file - cannot display"

        return JsonResponse({"success": True, "structure": structure})

    except Exception as e:
        return JsonResponse(
            {"success": False, "message": f"Error retrieving structure: {str(e)}"},
            status=500,
        )


@require_http_methods(["GET"])
def session_stats(request):
    """
    Get session statistics

    GET /api/collaboration/stats/

    Returns: {
        "success": true,
        "active_sessions": 5
    }
    """
    try:
        count = session_manager.get_session_count()

        return JsonResponse({"success": True, "active_sessions": count})

    except Exception as e:
        return JsonResponse(
            {"success": False, "message": f"Error retrieving stats: {str(e)}"},
            status=500,
        )


@require_http_methods(["GET"])
def list_all_sessions(request):
    """
    Get list of all active sessions

    GET /api/collaboration/sessions/

    Returns: {
        "success": true,
        "sessions": [
            {
                "session_id": "uuid",
                "initiator": "user_id",
                "created_at": "2025-11-27T...",
                "member_count": 3
            },
            ...
        ]
    }
    """
    try:
        sessions = session_manager.get_all_sessions()

        return JsonResponse({"success": True, "sessions": sessions})

    except Exception as e:
        return JsonResponse(
            {"success": False, "message": f"Error retrieving sessions: {str(e)}"},
            status=500,
        )


@csrf_exempt
@require_http_methods(["POST"])
def save_file(request, session_id):
    """
    Save edited file content to disk

    POST /api/collaboration/sessions/<session_id>/save/
    Body: {
        "filename": "example.py",
        "content": "file content here"
    }

    Returns: {
        "success": true,
        "message": "File saved successfully"
    }
    """
    try:
        # Check if user is authenticated
        if not request.user.is_authenticated:
            return JsonResponse({"success": False, "message": "请先登录"}, status=401)

        data = json.loads(request.body)
        filename = data.get("filename")
        content = data.get("content", "")

        if not filename:
            return JsonResponse(
                {"success": False, "message": "filename is required"},
                status=400,
            )

        # Verify session exists
        if not session_manager.session_exists(session_id):
            return JsonResponse(
                {"success": False, "message": "Session not found"}, status=404
            )

        # Save file to disk
        import os

        from django.conf import settings

        session_dir = os.path.join(
            settings.MEDIA_ROOT, "collaboration_sessions", session_id
        )
        os.makedirs(session_dir, exist_ok=True)

        file_path = os.path.join(session_dir, filename)

        # Security check: ensure file is within session directory
        if not os.path.abspath(file_path).startswith(os.path.abspath(session_dir)):
            return JsonResponse(
                {"success": False, "message": "Invalid filename"},
                status=400,
            )

        with open(file_path, "w", encoding="utf-8") as f:
            f.write(content)

        return JsonResponse({"success": True, "message": "File saved successfully"})

    except json.JSONDecodeError:
        return JsonResponse(
            {"success": False, "message": "Invalid JSON format"}, status=400
        )
    except Exception as e:
        return JsonResponse(
            {"success": False, "message": f"Error saving file: {str(e)}"},
            status=500,
        )


@require_http_methods(["GET"])
def collaboration_home(request):
    """
    实时协作首页
    显示协作会话管理界面
    """
    return render(request, "RealtimeCollaboration/collaboration_home.html")


@require_http_methods(["GET"])
def session_detail_page(request, session_id):
    """
    会话详情页面
    显示会话信息和成员列表
    """
    session = session_manager.get_session(session_id)

    if not session:
        return render(
            request,
            "RealtimeCollaboration/session_not_found.html",
            {"session_id": session_id},
            status=404,
        )

    members = session_manager.get_all_members(session_id)

    return render(
        request,
        "RealtimeCollaboration/session_detail.html",
        {"session": session, "members": members, "session_id": session_id},
    )
