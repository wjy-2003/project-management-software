"""
ASGI config for webapp project.

It exposes the ASGI callable as a module-level variable named ``application``.

For more information on this file, see
https://docs.djangoproject.com/en/5.2/howto/deployment/asgi/
"""

import os

from django.core.asgi import get_asgi_application
from channels.routing import ProtocolTypeRouter, URLRouter
from channels.auth import AuthMiddlewareStack
from channels.security.websocket import AllowedHostsOriginValidator

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "webapp.settings")

# 初始化 Django ASGI 应用
django_asgi_app = get_asgi_application()

# 导入 WebSocket 路由
from RealtimeCollaboration.routing import websocket_urlpatterns

application = ProtocolTypeRouter({
    "http": django_asgi_app,  # 处理 HTTP 请求
    "websocket": AllowedHostsOriginValidator(  # 验证来源主机
        AuthMiddlewareStack(  # 处理 WebSocket 请求
            URLRouter(
                websocket_urlpatterns
            )
        )
    ),
})
