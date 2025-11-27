from django.shortcuts import render
from django.views.generic import TemplateView

# from django.contrib.auth.mixins import LoginRequiredMixin  # 暂时注释掉


class DashboardView(TemplateView):  # LoginRequiredMixin,
    template_name = "webapp/dashboard.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        # 这里可以添加从数据库获取的实际数据
        return context


class ProjectListView(TemplateView):  # LoginRequiredMixin,
    template_name = "webapp/project_list.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        # 这里可以从ProjectManagement模型获取项目数据
        context["projects"] = []  # 暂时为空，后续连接数据库后填充
        return context


class RequirementListView(TemplateView):  # LoginRequiredMixin,
    template_name = "webapp/requirement_list.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        # 这里可以从数据库获取需求数据
        return context


class TeamManagementView(TemplateView):  # LoginRequiredMixin,
    template_name = "webapp/team_management.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        # 这里可以从TeamManagement模型获取团队数据
        return context


class VisualizationView(TemplateView):  # LoginRequiredMixin,
    template_name = "webapp/visualization.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        return context


class GitIntegrationView(TemplateView):  # LoginRequiredMixin,
    template_name = "webapp/git_integration.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        return context


class RealtimeCollabView(TemplateView):  # LoginRequiredMixin,
    template_name = "webapp/realtime_collab.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        return context


# 简单的视图函数用于重定向
def git_integration_redirect(request):
    """重定向到独立的Git集成界面"""
    return render(request, "webapp/git_integration.html")


def realtime_collab_redirect(request):
    """直接重定向到 CollabFrontend 应用"""
    from django.http import HttpResponseRedirect

    return HttpResponseRedirect("http://localhost:8082/")
