"""
HTTP URL 路由配置
定义 REST API 端点
"""
from django.urls import path
from . import views

app_name = 'collaboration'

urlpatterns = [
    # 会话管理
    path('sessions/create/', views.create_session, name='create_session'),
    path('sessions/<str:session_id>/', views.get_session, name='get_session'),
    path('sessions/<str:session_id>/join/', views.join_session, name='join_session'),
    path('sessions/<str:session_id>/leave/', views.leave_session, name='leave_session'),
    
    # 权限管理
    path('sessions/<str:session_id>/permissions/', views.update_permission, name='update_permission'),
    
    # 成员和结构
    path('sessions/<str:session_id>/members/', views.list_members, name='list_members'),
    path('sessions/<str:session_id>/structure/', views.get_structure, name='get_structure'),
    
    # 统计信息
    path('stats/', views.session_stats, name='session_stats'),
]
