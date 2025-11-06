"""
WebSocket 路由配置
定义 WebSocket URL 模式并映射到对应的 Consumer
"""
from django.urls import re_path
from . import consumers

websocket_urlpatterns = [
    # 支持两种形式：
    # /ws/collaboration/<session_id>/<member_id>/
    # /ws/collaboration/<session_id>/<member_id>/collab-room
    re_path(
        r"^ws/collaboration/(?P<session_id>[^/]+)/(?P<member_id>[^/]+)(?:/(?P<room>[^/]+))?/?$",
        consumers.CollaborationConsumer.as_asgi(),
    ),
]
