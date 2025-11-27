"""
HTTP URL routing configuration
Defines REST API endpoints
"""
from django.urls import path
from . import views

app_name = 'collaboration'

urlpatterns = [
    # Session management
    path('sessions/create/', views.create_session, name='create_session'),
    path('sessions/<str:session_id>/', views.get_session, name='get_session'),
    path('sessions/<str:session_id>/join/', views.join_session, name='join_session'),
    path('sessions/<str:session_id>/leave/', views.leave_session, name='leave_session'),
    
    # Permission management
    path('sessions/<str:session_id>/permissions/', views.update_permission, name='update_permission'),
    
    # Members and structure
    path('sessions/<str:session_id>/members/', views.list_members, name='list_members'),
    path('sessions/<str:session_id>/structure/', views.get_structure, name='get_structure'),
    
    # Statistics
    path('stats/', views.session_stats, name='session_stats'),
]
