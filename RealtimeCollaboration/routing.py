"""
WebSocket Router
define WebSocket URL - Consumer
"""
from django.urls import re_path
from . import consumers

websocket_urlpatterns = [
    # /ws/collaboration/<session_id>/<member_id>/
    # /ws/collaboration/<session_id>/<member_id>/collab-room
    re_path(
        r"^ws/collaboration/(?P<session_id>[^/]+)/(?P<member_id>[^/]+)(?:/(?P<room>[^/]+))?/?$",
        consumers.CollaborationConsumer.as_asgi(),
    ),
]
