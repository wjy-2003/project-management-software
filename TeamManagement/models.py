from django.conf import settings
from django.core.exceptions import ValidationError
from django.db import models

class Permission(models.Model):
    code = models.CharField(max_length=64, unique=True)
    label = models.CharField(max_length=128)

    class Meta:
        verbose_name = "Permission"
        verbose_name_plural = "Permissions"

    def __str__(self):
        return self.label


class Role(models.Model):
    name = models.CharField(max_length=64, unique=True)
    description = models.TextField(blank=True)
    permissions = models.ManyToManyField(Permission, blank=True)

    class Meta:
        verbose_name = "Role"
        verbose_name_plural = "Roles"

    def __str__(self):
        return self.name

    def has_permission(self, perm_code: str) -> bool:
        return self.permissions.filter(code=perm_code).exists()


class Team(models.Model):
    name = models.CharField(max_length=128, unique=True)
    description = models.TextField(blank=True)
    owner = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="owned_teams",
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "Team"
        verbose_name_plural = "Teams"

    def __str__(self):
        return self.name


class TeamMember(models.Model):
    team = models.ForeignKey(Team, on_delete=models.CASCADE, related_name="members")
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="team_memberships")
    role = models.ForeignKey(Role, on_delete=models.PROTECT, related_name="members")
    is_active = models.BooleanField(default=True)
    joined_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "Team member"
        verbose_name_plural = "Team members"
        unique_together = ("team", "user")

    def __str__(self):
        return f"{self.user.get_username()} @ {self.team} ({self.role})"

    def has_permission(self, perm_code: str) -> bool:
        return self.is_active and self.role.has_permission(perm_code)


class ProjectAssignment(models.Model):
    membership = models.ForeignKey(
        TeamMember, on_delete=models.CASCADE, related_name="project_assignments"
    )
    project = models.ForeignKey(
        "ProjectManagement.Project", on_delete=models.CASCADE, related_name="team_assignments"
    )
    assigned_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "Project assignment"
        verbose_name_plural = "Project assignments"
        unique_together = ("membership", "project")


class TaskAssignment(models.Model):
    membership = models.ForeignKey(
        TeamMember, on_delete=models.CASCADE, related_name="task_assignments"
    )
    task = models.ForeignKey(
        "ProjectManagement.Task", on_delete=models.CASCADE, related_name="team_assignments"
    )
    assigned_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="assigned_tasks",
    )
    assigned_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "Task assignment"
        verbose_name_plural = "Task assignments"
        unique_together = ("membership", "task")

    def clean(self):
        if not self.membership.has_permission("assign_task"):
            raise ValidationError("Member lacks permission to assign tasks.")
