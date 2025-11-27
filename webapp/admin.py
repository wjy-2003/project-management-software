from django.contrib import admin
from django.shortcuts import redirect

# from django.urls import path


class CustomAdminSite(admin.AdminSite):
    """自定义 Admin Site，登录后重定向到项目列表"""

    def index(self, request, extra_context=None):
        """覆盖 admin 首页，重定向到项目列表"""
        return redirect("/projects/")


# 替换默认的 admin site
admin.site = CustomAdminSite()
admin.site.site_header = "项目管理系统"
admin.site.site_title = "项目管理"
admin.site.index_title = "管理后台"
