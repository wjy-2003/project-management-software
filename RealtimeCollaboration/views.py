# from django.shortcuts import render

"""
REST API 视图
提供会话管理的 HTTP 接口
"""
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods
import json
from .session_manager import session_manager


@csrf_exempt
@require_http_methods(["POST"])
def create_session(request):
    """
    创建新的协作会话
    
    POST /api/collaboration/sessions/create/
    Body: {
        "initiator": "user_id"
    }
    
    Returns: {
        "success": true,
        "session_id": "uuid",
        "message": "Session created successfully"
    }
    """
    try:
        data = json.loads(request.body)
        initiator = data.get('initiator')
        
        if not initiator:
            return JsonResponse({
                'success': False,
                'message': 'Initiator ID is required'
            }, status=400)
        
        session_id = session_manager.create_session(initiator)
        
        return JsonResponse({
            'success': True,
            'session_id': session_id,
            'message': 'Session created successfully'
        }, status=201)
    
    except json.JSONDecodeError:
        return JsonResponse({
            'success': False,
            'message': 'Invalid JSON format'
        }, status=400)
    except Exception as e:
        return JsonResponse({
            'success': False,
            'message': f'Error creating session: {str(e)}'
        }, status=500)


@require_http_methods(["GET"])
def get_session(request, session_id):
    """
    获取会话信息
    
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
            return JsonResponse({
                'success': False,
                'message': 'Session not found'
            }, status=404)
        
        # 获取成员列表
        members = session_manager.get_all_members(session_id)
        
        return JsonResponse({
            'success': True,
            'session': {
                'session_id': session['session_id'],
                'initiator': session['initiator'],
                'created_at': session['created_at'],
                'members': members,
                'structure': session['structure']
            }
        })
    
    except Exception as e:
        return JsonResponse({
            'success': False,
            'message': f'Error retrieving session: {str(e)}'
        }, status=500)


@csrf_exempt
@require_http_methods(["POST"])
def join_session(request, session_id):
    """
    加入协作会话
    
    POST /api/collaboration/sessions/<session_id>/join/
    Body: {
        "member_id": "user_id",
        "role": "editor"  // 可选: "editor" 或 "viewer"，默认 "viewer"
    }
    
    Returns: {
        "success": true,
        "message": "Joined session successfully"
    }
    """
    try:
        data = json.loads(request.body)
        member_id = data.get('member_id')
        role = data.get('role', 'viewer')
        
        if not member_id:
            return JsonResponse({
                'success': False,
                'message': 'Member ID is required'
            }, status=400)
        
        if role not in ['editor', 'viewer']:
            return JsonResponse({
                'success': False,
                'message': 'Invalid role. Must be "editor" or "viewer"'
            }, status=400)
        
        if not session_manager.session_exists(session_id):
            return JsonResponse({
                'success': False,
                'message': 'Session not found'
            }, status=404)
        
        success = session_manager.add_member(session_id, member_id, role)
        
        if success:
            return JsonResponse({
                'success': True,
                'message': 'Joined session successfully'
            })
        else:
            return JsonResponse({
                'success': False,
                'message': 'Failed to join session'
            }, status=500)
    
    except json.JSONDecodeError:
        return JsonResponse({
            'success': False,
            'message': 'Invalid JSON format'
        }, status=400)
    except Exception as e:
        return JsonResponse({
            'success': False,
            'message': f'Error joining session: {str(e)}'
        }, status=500)


@csrf_exempt
@require_http_methods(["POST"])
def leave_session(request, session_id):
    """
    离开协作会话
    
    POST /api/collaboration/sessions/<session_id>/leave/
    Body: {
        "member_id": "user_id"
    }
    
    Returns: {
        "success": true,
        "message": "Left session successfully",
        "session_destroyed": false
    }
    """
    try:
        data = json.loads(request.body)
        member_id = data.get('member_id')
        
        if not member_id:
            return JsonResponse({
                'success': False,
                'message': 'Member ID is required'
            }, status=400)
        
        session_destroyed = session_manager.remove_member(session_id, member_id)
        
        return JsonResponse({
            'success': True,
            'message': 'Left session successfully',
            'session_destroyed': session_destroyed
        })
    
    except json.JSONDecodeError:
        return JsonResponse({
            'success': False,
            'message': 'Invalid JSON format'
        }, status=400)
    except Exception as e:
        return JsonResponse({
            'success': False,
            'message': f'Error leaving session: {str(e)}'
        }, status=500)


@csrf_exempt
@require_http_methods(["POST"])
def update_permission(request, session_id):
    """
    更新成员权限（仅发起者可调用）
    
    POST /api/collaboration/sessions/<session_id>/permissions/
    Body: {
        "initiator_id": "user_id",
        "member_id": "target_user_id",
        "role": "editor"  // "editor" 或 "viewer"
    }
    
    Returns: {
        "success": true,
        "message": "Permission updated successfully"
    }
    """
    try:
        data = json.loads(request.body)
        initiator_id = data.get('initiator_id')
        member_id = data.get('member_id')
        role = data.get('role')
        
        if not all([initiator_id, member_id, role]):
            return JsonResponse({
                'success': False,
                'message': 'initiator_id, member_id, and role are required'
            }, status=400)
        
        if role not in ['editor', 'viewer']:
            return JsonResponse({
                'success': False,
                'message': 'Invalid role. Must be "editor" or "viewer"'
            }, status=400)
        
        # 验证是否为发起者
        if not session_manager.is_initiator(session_id, initiator_id):
            return JsonResponse({
                'success': False,
                'message': 'Permission denied: only initiator can change permissions'
            }, status=403)
        
        success = session_manager.update_member_role(
            session_id, member_id, role
        )
        
        if success:
            return JsonResponse({
                'success': True,
                'message': 'Permission updated successfully'
            })
        else:
            return JsonResponse({
                'success': False,
                'message': 'Failed to update permission. Member may not exist.'
            }, status=400)
    
    except json.JSONDecodeError:
        return JsonResponse({
            'success': False,
            'message': 'Invalid JSON format'
        }, status=400)
    except Exception as e:
        return JsonResponse({
            'success': False,
            'message': f'Error updating permission: {str(e)}'
        }, status=500)


@require_http_methods(["GET"])
def list_members(request, session_id):
    """
    获取会话成员列表
    
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
            return JsonResponse({
                'success': False,
                'message': 'Session not found'
            }, status=404)
        
        members = session_manager.get_all_members(session_id)
        
        return JsonResponse({
            'success': True,
            'members': members
        })
    
    except Exception as e:
        return JsonResponse({
            'success': False,
            'message': f'Error retrieving members: {str(e)}'
        }, status=500)


@require_http_methods(["GET"])
def get_structure(request, session_id):
    """
    获取文件夹结构
    
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
            return JsonResponse({
                'success': False,
                'message': 'Session not found'
            }, status=404)
        
        return JsonResponse({
            'success': True,
            'structure': structure
        })
    
    except Exception as e:
        return JsonResponse({
            'success': False,
            'message': f'Error retrieving structure: {str(e)}'
        }, status=500)


@require_http_methods(["GET"])
def session_stats(request):
    """
    获取会话统计信息
    
    GET /api/collaboration/stats/
    
    Returns: {
        "success": true,
        "active_sessions": 5
    }
    """
    try:
        count = session_manager.get_session_count()
        
        return JsonResponse({
            'success': True,
            'active_sessions': count
        })
    
    except Exception as e:
        return JsonResponse({
            'success': False,
            'message': f'Error retrieving stats: {str(e)}'
        }, status=500)
