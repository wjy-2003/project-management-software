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
from django.urls import include, path
from django.views.generic import RedirectView

from .admin import custom_admin_site

urlpatterns = [
    path("", RedirectView.as_view(url="/login/", permanent=False)),
    # 使用自定义的 AdminSite 处理登录与后台入口
    path("login/", custom_admin_site.urls),
    path("admin/", RedirectView.as_view(url="/projects/", permanent=False)),
    path("api/collaboration/", include("RealtimeCollaboration.urls")),
    path("git/", include("GitIntegration.urls")),
    path("projects/", include("ProjectManagement.urls")),
    path("teams/", include("TeamManagement.urls")),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
