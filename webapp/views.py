from django.contrib import messages
from django.contrib.auth import get_user_model
from django.contrib.auth import views as auth_views
from django.contrib.auth.forms import AuthenticationForm
from django.http import HttpResponseRedirect
from django.shortcuts import render
from django.urls import reverse
from django.views.generic import TemplateView

from ProjectManagement.models import Project, Task
from TeamManagement.models import Team, TeamMember

User = get_user_model()


class DashboardView(TemplateView):  # LoginRequiredMixin,
    template_name = "webapp/dashboard_simple.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        # 获取项目数据
        context["projects"] = Project.objects.all()
        # 获取团队数据
        context["teams"] = Team.objects.all()
        # 获取团队成员
        context["team_members"] = TeamMember.objects.select_related(
            "user", "role", "team"
        ).all()
        return context


class ProjectDetailView(TemplateView):  # LoginRequiredMixin,
    template_name = "webapp/project_detail.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        # 获取项目详情
        project_id = kwargs.get("pk")
        if project_id:
            try:
                context["project"] = Project.objects.get(id=project_id)
            except Project.DoesNotExist:
                context["project"] = None
        return context


class ProjectListView(TemplateView):  # LoginRequiredMixin,
    template_name = "webapp/project_list_unified.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        # 获取项目数据
        context["projects"] = Project.objects.all()
        # 添加状态标签映射
        status_labels = {
            "planning": {"label": "规划中", "class": "info"},
            "in_progress": {"label": "进行中", "class": "primary"},
            "completed": {"label": "已完成", "class": "success"},
            "suspended": {"label": "已暂停", "class": "warning"},
            "cancelled": {"label": "已取消", "class": "danger"},
        }

        for project in context["projects"]:
            status_info = status_labels.get(
                project.status, {"label": "未知", "class": "secondary"}
            )
            project.status_label = status_info["label"]
            project.status_class = status_info["class"]

        return context


class RequirementListView(TemplateView):  # LoginRequiredMixin,
    template_name = "webapp/requirement_list.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        # 这里可以从数据库获取需求数据
        return context


class TeamManagementView(TemplateView):  # LoginRequiredMixin,
    template_name = "webapp/team_management_unified.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        # 获取团队数据
        context["teams"] = Team.objects.all()
        # 获取团队成员
        context["team_members"] = TeamMember.objects.select_related(
            "user", "role", "team"
        ).all()
        return context


class VisualizationView(TemplateView):  # LoginRequiredMixin,
    template_name = "webapp/visualization.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        # 获取项目数据
        projects = Project.objects.all()
        context["projects"] = projects

        # 计算项目状态统计
        project_status = {
            "planning": projects.filter(status="planning").count(),
            "in_progress": projects.filter(status="in_progress").count(),
            "completed": projects.filter(status="completed").count(),
            "suspended": projects.filter(status="suspended").count(),
            "cancelled": projects.filter(status="cancelled").count(),
        }
        context["project_status"] = project_status
        context["completed_projects"] = project_status["completed"]

        # 获取任务数据
        tasks = Task.objects.all()
        context["total_tasks"] = tasks.count()

        # 计算任务状态统计
        task_status = {
            "not_started": tasks.filter(status="not_started").count(),
            "in_progress": tasks.filter(status="in_progress").count(),
            "completed": tasks.filter(status="completed").count(),
            "suspended": tasks.filter(status="suspended").count(),
        }
        context["task_status"] = task_status

        # 工时统计
        total_estimated = sum(p.estimated_hours or 0 for p in projects)
        total_consumed = sum(p.consumed_hours or 0 for p in projects)
        total_remaining = sum(p.remaining_hours or 0 for p in projects)

        context["total_estimated_hours"] = total_estimated
        context["total_consumed_hours"] = total_consumed
        context["total_remaining_hours"] = total_remaining

        # 团队数据
        team_members = TeamMember.objects.select_related("user", "role", "team").all()
        context["team_members"] = team_members

        # 团队角色统计（示例数据，因为Role模型可能还没有数据）
        context["team_role_count"] = {
            "dev": team_members.filter(role__name__icontains="开发").count() or 8,
            "manager": team_members.filter(role__name__icontains="经理").count() or 2,
            "tester": team_members.filter(role__name__icontains="测试").count() or 3,
            "pm": team_members.filter(role__name__icontains="产品").count() or 2,
        }

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

    return HttpResponseRedirect("http://localhost:3000/")


class CustomLoginView(auth_views.LoginView):
    """自定义登录视图"""

    template_name = "webapp/login.html"
    authentication_form = AuthenticationForm
    redirect_authenticated_user = True

    def get_success_url(self):
        """登录成功后重定向到仪表板"""
        return reverse("dashboard")

    def form_invalid(self, form):
        """表单验证失败时添加错误消息"""
        messages.error(self.request, "用户名或密码错误，请重试。")
        return super().form_invalid(form)
