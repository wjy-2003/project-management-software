from django import forms

from .models import Document, Project, Task


class DocumentForm(forms.ModelForm):
    class Meta:
        model = Document
        fields = ["title", "file", "description"]
        widgets = {
            "description": forms.Textarea(attrs={"rows": 3}),
        }


class ProjectForm(forms.ModelForm):
    class Meta:
        model = Project
        fields = [
            "project_number",
            "title",
            "description",
            "status",
            "planned_start_date",
            "planned_end_date",
            "actual_start_date",
            "actual_end_date",
            "estimated_hours",
            "consumed_hours",
            "available_workdays",
            "team_members",
            #           'documents',
        ]
        widgets = {
            "planned_start_date": forms.DateInput(attrs={"type": "date"}),
            "planned_end_date": forms.DateInput(attrs={"type": "date"}),
            "actual_start_date": forms.DateInput(attrs={"type": "date"}),
            "actual_end_date": forms.DateInput(attrs={"type": "date"}),
            "description": forms.Textarea(attrs={"rows": 4}),
        }


class TaskForm(forms.ModelForm):
    class Meta:
        model = Task
        fields = [
            "title",
            "description",
            "status",
            "assigned_to",
            "planned_start_date",
            "due_date",
            "actual_start_date",
            "actual_end_date",
            "estimated_hours",
            "consumed_hours",
        ]
        widgets = {
            "description": forms.Textarea(attrs={"rows": 4}),
            "planned_start_date": forms.DateInput(attrs={"type": "date"}),
            "due_date": forms.DateInput(attrs={"type": "date"}),
            "actual_start_date": forms.DateInput(attrs={"type": "date"}),
            "actual_end_date": forms.DateInput(attrs={"type": "date"}),
        }
        help_texts = {
            "planned_start_date": "计划开始工作的日期",
            "due_date": "预计完成的截止日期",
            "estimated_hours": "预计完成任务所需的工时",
            "consumed_hours": "已经花费的工时",
        }

    def __init__(self, project=None, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if project:
            # 只显示该项目的团队成员作为可选的负责人
            self.fields["assigned_to"].queryset = project.team_members.all()
            self.fields["assigned_to"].empty_label = "选择负责人"
