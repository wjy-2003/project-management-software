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


# ==================== VISUALIZATION VIEWS ====================

def project_progress_chart(request, project_number):
    """项目进度图表 - 显示项目总体进度和工时消耗情况"""
    from datetime import timedelta

    project = get_object_or_404(Project, project_number=project_number)
    tasks = project.tasks.all()

    # 计算任务状态分布
    task_status_counts = {}
    for status_choice in Task.STATUS_CHOICES:
        status_key = status_choice[0]
        status_label = status_choice[1]
        count = tasks.filter(status=status_key).count()
        task_status_counts[status_label] = count

    # 计算进度数据
    total_estimated_hours = float(project.estimated_hours)
    consumed_hours = float(project.consumed_hours)
    remaining_hours = float(project.remaining_hours)
    progress_percentage = project.get_project_progress()

    # 工时数据用于饼图
    hours_data = {
        '已消耗工时': round(consumed_hours, 1),
        '剩余工时': round(max(0, remaining_hours), 1)
    }

    context = {
        'project': project,
        'task_status_counts': task_status_counts,
        'total_tasks': tasks.count(),
        'completed_tasks': tasks.filter(status='completed').count(),
        'hours_data': hours_data,
        'total_estimated_hours': round(total_estimated_hours, 1),
        'consumed_hours': round(consumed_hours, 1),
        'remaining_hours': round(max(0, remaining_hours), 1),
        'progress_percentage': round(progress_percentage, 1),
    }

    return render(request, 'projectmanagement/visualization/project_progress.html', context)


def project_burndown_chart(request, project_number):
    """项目燃尽图 - 基于工时的项目燃尽图表"""
    from datetime import datetime, timedelta, date
    import json

    project = get_object_or_404(Project, project_number=project_number)
    tasks = project.tasks.all()

    # 确定日期范围（从实际开始日期或计划开始日期到今天或计划结束日期）
    start_date = project.actual_start_date or project.planned_start_date
    end_date = project.actual_end_date or project.planned_end_date

    if not start_date:
        start_date = project.planned_start_date
    if not end_date:
        end_date = project.planned_end_date

    # 如果项目还没完成，用今天作为结束日期
    if project.status not in ['completed', 'cancelled'] and date.today() < end_date:
        end_date = date.today()

    # 生成日期列表
    if start_date and end_date:
        delta = end_date - start_date
        dates = [(start_date + timedelta(days=i)).strftime('%Y-%m-%d')
                for i in range(delta.days + 1)]

        total_hours = float(project.estimated_hours)

        # 计算理想燃尽线（线性递减）
        ideal_burndown = []
        for i, date_str in enumerate(dates):
            remaining = total_hours - (total_hours * i / len(dates))
            ideal_burndown.append(round(max(0, remaining), 1))

        # 计算实际燃尽线（基于任务完成情况）
        actual_burndown = []
        for current_date_str in dates:
            current_date = datetime.strptime(current_date_str, '%Y-%m-%d').date()

            # 计算到当前日期为止完成的工时
            completed_hours = 0
            completed_tasks = tasks.filter(
                status='completed',
                actual_end_date__lte=current_date
            )
            for task in completed_tasks:
                completed_hours += float(task.estimated_hours)

            remaining = total_hours - completed_hours
            actual_burndown.append(round(max(0, remaining), 1))

        context = {
            'project': project,
            'dates': json.dumps(dates),
            'ideal_burndown': json.dumps(ideal_burndown),
            'actual_burndown': json.dumps(actual_burndown),
            'start_date': start_date.strftime('%Y-%m-%d'),
            'end_date': end_date.strftime('%Y-%m-%d'),
        }
    else:
        context = {
            'project': project,
            'error': '缺少项目日期信息，无法生成燃尽图'
        }

    return render(request, 'projectmanagement/visualization/project_burndown.html', context)


def team_workload_chart(request, project_number):
    """团队工作负载图表 - 显示团队成员的任务分配和工时情况"""
    project = get_object_or_404(Project, project_number=project_number)

    # 获取项目成员及其任务
    team_data = []
    total_assigned_hours = 0

    for member in project.team_members.all():
        member_tasks = project.tasks.filter(assigned_to=member)

        # 计算该成员的工时
        assigned_hours = sum(float(task.estimated_hours) for task in member_tasks)
        completed_hours = sum(float(task.estimated_hours)
                            for task in member_tasks.filter(status='completed'))

        team_data.append({
            'member_name': member.user.username,
            'member_role': member.role,
            'total_tasks': member_tasks.count(),
            'completed_tasks': member_tasks.filter(status='completed').count(),
            'assigned_hours': round(assigned_hours, 1),
            'completed_hours': round(completed_hours, 1),
            'completion_rate': round((completed_hours / assigned_hours * 100) if assigned_hours > 0 else 0, 1)
        })

        total_assigned_hours += assigned_hours

    # 按分配工时排序
    team_data.sort(key=lambda x: x['assigned_hours'], reverse=True)

    context = {
        'project': project,
        'team_data': team_data,
        'total_assigned_hours': round(total_assigned_hours, 1),
        'total_team_members': len(team_data),
    }

    return render(request, 'projectmanagement/visualization/team_workload.html', context)


def task_timeline_chart(request, project_number):
    """任务时间线图表 - 显示任务的开始和结束时间分布"""
    from datetime import datetime, timedelta
    import json

    project = get_object_or_404(Project, project_number=project_number)
    tasks = project.tasks.all()

    # 准备任务数据用于时间线图表
    timeline_data = []
    for task in tasks:
        # 确定开始和结束日期
        start_date = task.actual_start_date or task.planned_start_date
        end_date = task.actual_end_date or task.due_date

        if start_date:
            timeline_data.append({
                'title': task.title,
                'start_date': start_date.strftime('%Y-%m-%d'),
                'end_date': end_date.strftime('%Y-%m-%d') if end_date else None,
                'status': task.get_status_display(),
                'assigned_to': task.assigned_to.user.username if task.assigned_to else '未分配',
                'estimated_hours': float(task.estimated_hours)
            })

    # 按开始日期排序
    timeline_data.sort(key=lambda x: x['start_date'])

    # 计算每月任务完成情况
    monthly_completion = {}
    for task in tasks.filter(status='completed'):
        if task.actual_end_date:
            month_key = task.actual_end_date.strftime('%Y-%m')
            if month_key not in monthly_completion:
                monthly_completion[month_key] = 0
            monthly_completion[month_key] += 1

    context = {
        'project': project,
        'timeline_data': json.dumps(timeline_data),
        'timeline_count': len(timeline_data),
        'monthly_completion': json.dumps(monthly_completion),
        'total_tasks': tasks.count(),
        'completed_tasks': tasks.filter(status='completed').count(),
    }

    return render(request, 'projectmanagement/visualization/task_timeline.html', context)


def project_dashboard(request, project_number):
    """项目仪表板 - 综合显示项目的各种可视化数据"""
    project = get_object_or_404(Project, project_number=project_number)
    tasks = project.tasks.all()

    # 基础统计数据
    total_tasks = tasks.count()
    completed_tasks = tasks.filter(status='completed').count()
    in_progress_tasks = tasks.filter(status='in_progress').count()
    not_started_tasks = tasks.filter(status='not_started').count()
    suspended_tasks = tasks.filter(status='suspended').count()

    # 工时统计
    total_estimated_hours = float(project.estimated_hours)
    consumed_hours = float(project.consumed_hours)
    remaining_hours = float(project.remaining_hours)

    # 团队统计
    team_members = project.team_members.count()
    assigned_members = tasks.values('assigned_to').distinct().count()

    # 任务优先级和状态统计（如果有的话）
    task_status_distribution = []
    for status_choice in Task.STATUS_CHOICES:
        count = tasks.filter(status=status_choice[0]).count()
        if count > 0:
            task_status_distribution.append({
                'status': status_choice[1],
                'count': count,
                'percentage': round((count / total_tasks * 100) if total_tasks > 0 else 0, 1)
            })

    context = {
        'project': project,
        'total_tasks': total_tasks,
        'completed_tasks': completed_tasks,
        'in_progress_tasks': in_progress_tasks,
        'not_started_tasks': not_started_tasks,
        'suspended_tasks': suspended_tasks,
        'total_estimated_hours': round(total_estimated_hours, 1),
        'consumed_hours': round(consumed_hours, 1),
        'remaining_hours': round(max(0, remaining_hours), 1),
        'progress_percentage': round(project.get_project_progress(), 1),
        'team_members': team_members,
        'assigned_members': assigned_members,
        'task_status_distribution': task_status_distribution,
    }

    return render(request, 'projectmanagement/visualization/project_dashboard.html', context)
