import json

from django.contrib import messages
from django.http import JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone
from django.views.decorators.http import require_http_methods

from .forms import DocumentForm, ProjectForm, TaskForm
from .models import Document, Project, Task, TeamMember


def project_list(request):
    projects = Project.objects.all()
    context = {
        "projects": projects,
    }
    return render(request, "projectmanagement/project_list.html", context)


def project_create(request):
    if request.method == "POST":
        form = ProjectForm(request.POST)
        if form.is_valid():
            project = form.save()
            # 设置其他字段的初始值
            project.consumed_hours = 0
            project.remaining_hours = project.estimated_hours
            project.available_hours = (
                project.available_workdays * 8
            )  # 假设每天8小时工作时间
            project.save()
            return redirect("projectmanagement:project_list")
    else:
        form = ProjectForm()

    return render(
        request,
        "projectmanagement/project_form.html",
        {"form": form, "title": "新建项目"},
    )


def project_info(request, project_number):
    project = get_object_or_404(Project, project_number=project_number)
    # If Task has a foreign key to Project (not required), prefer that; otherwise show tasks assigned to team members
    if hasattr(Task, "project"):
        tasks = Task.objects.filter(project=project)
    elif hasattr(Task, "assigned_to"):
        tasks = Task.objects.filter(assigned_to__in=project.team_members.all())
    else:
        tasks = project.tasks.all()

    context = {
        "project": project,
        "team_members": project.team_members.all(),
        "documents": project.documents.all(),
        "tasks": tasks,
        "progress": project.get_project_progress(),
    }
    return render(request, "projectmanagement/project_info.html", context)


def project_cancel(request, project_number):
    project = get_object_or_404(Project, project_number=project_number)
    project.status = "cancelled"
    project.save()
    return redirect("projectmanagement:project_list")


def project_pause(request, project_number):
    project = get_object_or_404(Project, project_number=project_number)
    if project.status == "in_progress":
        project.status = "suspended"
        project.save()
    return redirect("projectmanagement:project_list")


def project_resume(request, project_number):
    project = get_object_or_404(Project, project_number=project_number)
    if project.status == "suspended":
        project.status = "in_progress"
        project.save()
    return redirect("projectmanagement:project_list")


def project_edit(request, project_number):
    project = get_object_or_404(Project, project_number=project_number)
    if request.method == "POST":
        form = ProjectForm(request.POST, instance=project)
        if form.is_valid():
            project = form.save(commit=False)
            # 更新剩余工时
            project.remaining_hours = max(
                0, project.estimated_hours - project.consumed_hours
            )
            # 更新可用工时（假设每天8小时工作时间）
            project.available_hours = project.available_workdays * 8
            # 如果状态改为"进行中"且没有实际开始时间，则设置为当前日期
            if project.status == "in_progress" and not project.actual_start_date:
                project.actual_start_date = timezone.now().date()
            # 如果状态改为"已完成"且没有实际结束时间，则设置为当前日期
            if project.status == "completed" and not project.actual_end_date:
                project.actual_end_date = timezone.now().date()
            project.save()
            form.save_m2m()  # 保存多对多字段
            return redirect(
                "projectmanagement:project_info", project_number=project.project_number
            )
    else:
        form = ProjectForm(instance=project)

    return render(
        request,
        "projectmanagement/project_edit.html",
        {"form": form, "project": project},
    )


def task_create(request, project_number):
    project = get_object_or_404(Project, project_number=project_number)
    if request.method == "POST":
        form = TaskForm(None, request.POST)
        if form.is_valid():
            task = form.save(commit=False)
            task.project = project
            task.save()
            messages.success(request, "任务创建成功！")
            return redirect(
                "projectmanagement:project_info", project_number=project_number
            )
    else:
        form = TaskForm(project=project)

    return render(
        request,
        "projectmanagement/task_form.html",
        {"form": form, "project": project, "title": "新建任务"},
    )


def task_edit(request, project_number, task_id):
    project = get_object_or_404(Project, project_number=project_number)
    task = get_object_or_404(Task, id=task_id)

    if request.method == "POST":
        form = TaskForm(None, request.POST, instance=task)
        if form.is_valid():
            task = form.save(commit=False)
            task.project = project
            task.save()
            messages.success(request, "任务更新成功！")
            return redirect(
                "projectmanagement:project_info", project_number=project_number
            )
    else:
        form = TaskForm(project=project, instance=task)

    return render(
        request,
        "projectmanagement/task_form.html",
        {"form": form, "project": project, "task": task, "title": "编辑任务"},
    )


def task_delete(request, project_number, task_id):
    task = get_object_or_404(Task, id=task_id)
    task.delete()
    messages.success(request, "任务删除成功！")
    return redirect("projectmanagement:project_info", project_number=project_number)


def task_start(request, project_number, task_id):
    task = get_object_or_404(Task, id=task_id)
    if task.status == "not_started":
        task.status = "in_progress"
        task.actual_start_date = timezone.now().date()
        task.save(force_status=True)
        messages.success(request, "任务已开始！")
    return redirect("projectmanagement:project_info", project_number=project_number)


def task_suspend(request, project_number, task_id):
    task = get_object_or_404(Task, id=task_id)
    if task.status == "in_progress":
        task.status = "suspended"
        task.save(force_status=True)
        messages.success(request, "任务已暂停！")
    return redirect("projectmanagement:project_info", project_number=project_number)


def task_complete(request, project_number, task_id):
    task = get_object_or_404(Task, id=task_id)
    if task.status in ["in_progress", "suspended"]:
        # 更新状态为完成，并设置当前日期作为默认实际完成日期
        task.status = "completed"
        task.actual_end_date = timezone.now().date()
        task.save(force_status=True)
        # 重定向到任务编辑表单
        messages.info(
            request, "请确认任务的实际开始时间和完成时间，并点击保存完成任务。"
        )
        return redirect(
            "projectmanagement:task_edit",
            project_number=project_number,
            task_id=task_id,
        )
    return redirect("projectmanagement:project_info", project_number=project_number)


def document_upload(request, project_number):
    project = get_object_or_404(Project, project_number=project_number)
    if request.method == "POST":
        form = DocumentForm(request.POST, request.FILES)
        if form.is_valid():
            document = form.save()
            project.documents.add(document)
            messages.success(request, "文档上传成功！")
            return redirect(
                "projectmanagement:project_info", project_number=project_number
            )
    else:
        form = DocumentForm()

    return render(
        request,
        "projectmanagement/document_form.html",
        {"form": form, "project": project, "title": "上传文档"},
    )


def document_delete(request, project_number, document_id):
    document = get_object_or_404(Document, id=document_id)
    document.delete()
    messages.success(request, "文档删除成功！")
    return redirect("projectmanagement:project_info", project_number=project_number)


@require_http_methods(["GET", "POST"])
def project_members_manage(request, project_number):
    """管理项目成员 - 通过选择团队批量添加成员"""
    from TeamManagement.models import Team as TMTeam

    project = get_object_or_404(Project, project_number=project_number)

    if request.method == "POST":
        try:
            data = json.loads(request.body)
            selected_team_ids = data.get("team_ids", [])

            # 获取选中的团队
            teams = TMTeam.objects.filter(id__in=selected_team_ids).prefetch_related(
                "members__user"
            )

            added_count = 0
            for team in teams:
                for tm_member in team.members.all():
                    # 检查该用户是否已经是该项目的成员
                    existing = project.team_members.filter(user=tm_member.user).exists()

                    if not existing:
                        # 创建项目团队成员
                        member = TeamMember.objects.create(
                            user=tm_member.user,
                            role=tm_member.role.name if tm_member.role else "成员",
                            join_date=timezone.now(),
                        )
                        project.team_members.add(member)
                        added_count += 1

            return JsonResponse(
                {
                    "success": True,
                    "message": f"成功添加 {added_count} 名成员到项目",
                    "added_count": added_count,
                }
            )

        except Exception as e:
            return JsonResponse(
                {"success": False, "message": f"添加成员失败: {str(e)}"}, status=400
            )

    # GET 请求 - 显示团队树
    teams = TMTeam.objects.all().prefetch_related("members__user", "members__role")

    context = {
        "project": project,
        "teams": teams,
    }

    return render(request, "projectmanagement/members_manage.html", context)
