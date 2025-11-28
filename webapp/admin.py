from django.contrib import admin
from django.shortcuts import redirect


class CustomAdminSite(admin.AdminSite):
    """自定义 Admin Site，登录后重定向到项目列表"""

    def index(self, request, extra_context=None):
        """覆盖 admin 首页，重定向到项目列表"""
        return redirect("/projects/")


# 创建自定义的 AdminSite 实例（不要覆盖默认 admin.site）
custom_admin_site = CustomAdminSite(name="custom_admin")
custom_admin_site.site_header = "项目管理系统"
custom_admin_site.site_title = "项目管理"
custom_admin_site.index_title = "管理后台"
