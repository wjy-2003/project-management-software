"""
URL configuration for webapp project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/5.2/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""

from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin
from django.contrib.auth import views as auth_views
from django.urls import path

from . import views

urlpatterns = [
    # 登录页面暂时使用admin
    path("login/", admin.site.urls),
    # 主页重定向到仪表板
    path("", views.DashboardView.as_view(), name="home"),
    # 主要功能页面
    path("dashboard/", views.DashboardView.as_view(), name="dashboard"),
    # 项目管理
    path("projects/", views.ProjectListView.as_view(), name="project_list"),
    path(
        "project/<int:pk>/",
        views.TemplateView.as_view(template_name="webapp/project_detail.html"),
        name="project_detail",
    ),
    path(
        "project/create/",
        views.TemplateView.as_view(template_name="webapp/project_create.html"),
        name="project_create",
    ),
    path(
        "project/<int:pk>/edit/",
        views.TemplateView.as_view(template_name="webapp/project_edit.html"),
        name="project_edit",
    ),
    # 需求管理
    path("requirements/", views.RequirementListView.as_view(), name="requirement_list"),
    path(
        "requirement/create/",
        views.TemplateView.as_view(template_name="webapp/requirement_create.html"),
        name="requirement_create",
    ),
    path(
        "requirement/<int:pk>/",
        views.TemplateView.as_view(template_name="webapp/requirement_detail.html"),
        name="requirement_detail",
    ),
    # 团队管理
    path("team/", views.TeamManagementView.as_view(), name="team_management"),
    path(
        "team/member/add/",
        views.TemplateView.as_view(template_name="webapp/team_member_add.html"),
        name="team_member_add",
    ),
    # 可视化
    path("visualization/", views.VisualizationView.as_view(), name="visualization"),
    # 环境管理
    path(
        "environment/",
        views.TemplateView.as_view(template_name="webapp/environment_manage.html"),
        name="environment_manage",
    ),
    # Git集成和实时协作（重定向到独立界面）
    path("git/", views.git_integration_redirect, name="git_integration"),
    path("collab/", views.realtime_collab_redirect, name="realtime_collab"),
    # 登录/登出
    path("logout/", auth_views.LogoutView.as_view(next_page="login"), name="logout"),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
