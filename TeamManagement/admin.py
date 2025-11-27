from __future__ import annotations

from typing import Dict, Iterable, Optional, Set

from django.conf import settings
from django.contrib import admin
from django.db.models import QuerySet

from .models import (Permission, ProjectAssignment, Role, TaskAssignment, Team,
                     TeamMember)

DEFAULT_ADMIN_PERMISSION_CODES: Dict[str, str] = {
    "permission_admin": "permission_manage",
    "role_admin": "role_manage",
    "team_view_all": "team_view_all",
    "team_manage_all": "team_manage_all",
    "team_manage": "team_manage",
    "team_create": "team_create",
    "member_view_all": "teammember_view_all",
    "member_manage_all": "teammember_manage_all",
    "member_manage": "teammember_manage",
    "project_assign_all": "project_assign_all",
    "project_assign": "project_assign",
    "assign_task_all": "assign_task_all",
    "assign_task": "assign_task",
}

PERMISSION_CODES = getattr(
    settings, "TEAM_MANAGEMENT_ADMIN_PERMISSIONS", DEFAULT_ADMIN_PERMISSION_CODES
)
if not isinstance(PERMISSION_CODES, dict):
    PERMISSION_CODES = DEFAULT_ADMIN_PERMISSION_CODES


def _resolve_permission_code(key: Optional[str]) -> Optional[str]:
    if not key:
        return None
    return PERMISSION_CODES.get(key, key)


def _user_has_role_permission(
    user, code: Optional[str], team: Optional[Team] = None
) -> bool:
    if code is None:
        return True
    if not getattr(user, "is_authenticated", False):
        return False
    if getattr(user, "is_superuser", False):
        return True
    memberships = TeamMember.objects.filter(user=user, is_active=True)
    if team is not None:
        memberships = memberships.filter(team=team)
    return memberships.filter(role__permissions__code=code).exists()


def _get_owned_team_ids(user) -> Set[int]:
    if not getattr(user, "is_authenticated", False):
        return set()
    return set(Team.objects.filter(owner=user).values_list("id", flat=True))


def _get_team_ids_for_user(user, permission_key: Optional[str] = None) -> Set[int]:
    if not getattr(user, "is_authenticated", False):
        return set()
    if getattr(user, "is_superuser", False):
        return set(Team.objects.values_list("id", flat=True))
    team_ids = _get_owned_team_ids(user)
    memberships = TeamMember.objects.filter(user=user, is_active=True)
    code = _resolve_permission_code(permission_key)
    if code:
        memberships = memberships.filter(role__permissions__code=code)
    team_ids.update(memberships.values_list("team_id", flat=True))
    return team_ids


def _membership_team_id(
    membership_obj: Optional[TeamMember], membership_id: Optional[int]
) -> Optional[int]:
    if membership_obj is not None:
        team_id = getattr(membership_obj, "team_id", None)
        if team_id is not None:
            return team_id
    if membership_id is None:
        return None
    return (
        TeamMember.objects.filter(pk=membership_id)
        .values_list("team_id", flat=True)
        .first()
    )


class RoleProtectedAdmin(admin.ModelAdmin):
    module_permission_key: Optional[str] = None
    view_permission_key: Optional[str] = None
    add_permission_key: Optional[str] = None
    change_permission_key: Optional[str] = None
    delete_permission_key: Optional[str] = None

    def _is_staff(self, request) -> bool:
        user = request.user
        return getattr(user, "is_active", False) and getattr(user, "is_staff", False)

    def _has_permission(self, user, key: Optional[str]) -> bool:
        code = _resolve_permission_code(key)
        return _user_has_role_permission(user, code)

    def has_module_permission(self, request) -> bool:
        return self._is_staff(request) and self._has_permission(
            request.user, self.module_permission_key
        )

    def has_view_permission(self, request, obj=None) -> bool:
        if not self._is_staff(request):
            return False
        if obj is None:
            return self._has_permission(request.user, self.view_permission_key)
        if self._has_permission(request.user, self.view_permission_key):
            return True
        handler = getattr(self, "has_object_view_permission", None)
        if handler is None:
            return False
        return handler(request, obj)

    def has_add_permission(self, request) -> bool:
        return self._is_staff(request) and self._has_permission(
            request.user, self.add_permission_key
        )

    def has_change_permission(self, request, obj=None) -> bool:
        if not self._is_staff(request):
            return False
        if obj is None:
            return self._has_permission(request.user, self.change_permission_key)
        if self._has_permission(request.user, self.change_permission_key):
            return True
        handler = getattr(self, "has_object_change_permission", None)
        if handler is None:
            return False
        return handler(request, obj)

    def has_delete_permission(self, request, obj=None) -> bool:
        if not self._is_staff(request):
            return False
        if obj is None:
            return self._has_permission(request.user, self.delete_permission_key)
        if self._has_permission(request.user, self.delete_permission_key):
            return True
        handler = getattr(self, "has_object_delete_permission", None)
        if handler is None:
            return False
        return handler(request, obj)


class TeamScopedAdmin(RoleProtectedAdmin):
    team_permission_key: Optional[str] = None

    def has_module_permission(self, request) -> bool:
        if not self._is_staff(request):
            return False
        if getattr(request.user, "is_superuser", False):
            return True
        primary_key = self.module_permission_key or self.view_permission_key
        if primary_key:
            if self._has_permission(request.user, primary_key):
                return True
        allowed_ids = _get_team_ids_for_user(request.user)
        return bool(allowed_ids)

    def has_view_permission(self, request, obj=None) -> bool:
        if not self._is_staff(request):
            return False
        if getattr(request.user, "is_superuser", False):
            return True
        if obj is None:
            if self._has_permission(request.user, self.view_permission_key):
                return True
            allowed_ids = _get_team_ids_for_user(request.user)
            return bool(allowed_ids)
        if self._has_permission(request.user, self.view_permission_key):
            return True
        allowed_ids = _get_team_ids_for_user(request.user)
        return bool(self.get_object_team_ids(obj) & allowed_ids)

    def has_add_permission(self, request) -> bool:
        if not self._is_staff(request):
            return False
        if getattr(request.user, "is_superuser", False):
            return True
        if self._has_permission(request.user, self.add_permission_key):
            return True
        allowed_ids = _get_team_ids_for_user(request.user, self.team_permission_key)
        return bool(allowed_ids)

    def has_change_permission(self, request, obj=None) -> bool:
        if not self._is_staff(request):
            return False
        if getattr(request.user, "is_superuser", False):
            return True
        if obj is None:
            return True
        if self._has_permission(request.user, self.change_permission_key):
            return True
        allowed_ids = _get_team_ids_for_user(request.user, self.team_permission_key)
        return bool(self.get_object_team_ids(obj) & allowed_ids)

    def has_delete_permission(self, request, obj=None) -> bool:
        if not self._is_staff(request):
            return False
        if getattr(request.user, "is_superuser", False):
            return True
        if obj is None:
            return True
        if self._has_permission(request.user, self.delete_permission_key):
            return True
        allowed_ids = _get_team_ids_for_user(request.user, self.team_permission_key)
        return bool(self.get_object_team_ids(obj) & allowed_ids)

    def get_queryset(self, request):
        qs = super().get_queryset(request)
        if getattr(request.user, "is_superuser", False):
            return qs
        if self._has_permission(request.user, self.view_permission_key):
            return qs
        allowed_ids = _get_team_ids_for_user(request.user)
        if not allowed_ids:
            return qs.none()
        return self._filter_queryset_by_team_ids(qs, allowed_ids)

    def get_object_team_ids(self, obj) -> Set[int]:
        raise NotImplementedError

    def _filter_queryset_by_team_ids(
        self, qs: QuerySet, team_ids: Iterable[int]
    ) -> QuerySet:
        raise NotImplementedError


@admin.register(Permission)
class PermissionAdmin(RoleProtectedAdmin):
    module_permission_key = "permission_admin"
    view_permission_key = "permission_admin"
    add_permission_key = "permission_admin"
    change_permission_key = "permission_admin"
    delete_permission_key = "permission_admin"

    list_display = ("code", "label")
    search_fields = ("code", "label")
    ordering = ("code",)


@admin.register(Role)
class RoleAdmin(RoleProtectedAdmin):
    module_permission_key = "role_admin"
    view_permission_key = "role_admin"
    add_permission_key = "role_admin"
    change_permission_key = "role_admin"
    delete_permission_key = "role_admin"

    list_display = ("name", "description_preview", "permission_count")
    search_fields = ("name", "description")
    filter_horizontal = ("permissions",)

    @admin.display(description="Description")
    def description_preview(self, obj):
        if not obj.description:
            return ""
        if len(obj.description) <= 60:
            return obj.description
        return f"{obj.description[:57]}..."

    @admin.display(description="Permissions")
    def permission_count(self, obj) -> int:
        return obj.permissions.count()


@admin.register(Team)
class TeamAdmin(TeamScopedAdmin):
    module_permission_key = "team_view_all"
    view_permission_key = "team_view_all"
    add_permission_key = "team_create"
    change_permission_key = "team_manage_all"
    delete_permission_key = "team_manage_all"
    team_permission_key = "team_manage"

    list_display = ("name", "owner", "created_at")
    search_fields = ("name", "description", "owner__username", "owner__email")
    list_filter = ("owner",)
    readonly_fields = ("created_at",)
    ordering = ("name",)

    def has_add_permission(self, request) -> bool:
        if not self._is_staff(request):
            return False
        if getattr(request.user, "is_superuser", False):
            return True
        return self._has_permission(request.user, self.add_permission_key)

    def get_object_team_ids(self, obj) -> Set[int]:
        if obj.pk is None:
            return set()
        return {obj.pk}

    def _filter_queryset_by_team_ids(
        self, qs: QuerySet, team_ids: Iterable[int]
    ) -> QuerySet:
        return qs.filter(id__in=list(team_ids))


@admin.register(TeamMember)
class TeamMemberAdmin(TeamScopedAdmin):
    module_permission_key = "member_view_all"
    view_permission_key = "member_view_all"
    add_permission_key = "member_manage_all"
    change_permission_key = "member_manage_all"
    delete_permission_key = "member_manage_all"
    team_permission_key = "member_manage"

    list_display = ("team", "user", "role", "is_active", "joined_at")
    list_filter = ("team", "role", "is_active")
    search_fields = (
        "team__name",
        "user__username",
        "user__first_name",
        "user__last_name",
        "role__name",
    )
    readonly_fields = ("joined_at",)

    def formfield_for_foreignkey(self, db_field, request, **kwargs):
        if db_field.name == "team" and not getattr(request.user, "is_superuser", False):
            allowed_ids = _get_team_ids_for_user(request.user, self.team_permission_key)
            kwargs["queryset"] = (
                Team.objects.filter(id__in=list(allowed_ids))
                if allowed_ids
                else Team.objects.none()
            )
        return super().formfield_for_foreignkey(db_field, request, **kwargs)

    def get_object_team_ids(self, obj) -> Set[int]:
        if obj.team_id is None:
            return set()
        return {obj.team_id}

    def _filter_queryset_by_team_ids(
        self, qs: QuerySet, team_ids: Iterable[int]
    ) -> QuerySet:
        return qs.filter(team_id__in=list(team_ids))


@admin.register(ProjectAssignment)
class ProjectAssignmentAdmin(TeamScopedAdmin):
    add_permission_key = "project_assign_all"
    change_permission_key = "project_assign_all"
    delete_permission_key = "project_assign_all"
    team_permission_key = "project_assign"

    list_display = ("membership", "project", "assigned_at")
    list_filter = ("membership__team",)
    search_fields = (
        "membership__team__name",
        "membership__user__username",
        "project__id",
    )
    readonly_fields = ("assigned_at",)

    def formfield_for_foreignkey(self, db_field, request, **kwargs):
        if db_field.name == "membership" and not getattr(
            request.user, "is_superuser", False
        ):
            allowed_ids = _get_team_ids_for_user(request.user, self.team_permission_key)
            kwargs["queryset"] = (
                TeamMember.objects.filter(team_id__in=list(allowed_ids), is_active=True)
                if allowed_ids
                else TeamMember.objects.none()
            )
        return super().formfield_for_foreignkey(db_field, request, **kwargs)

    def get_object_team_ids(self, obj) -> Set[int]:
        membership = getattr(obj, "membership", None)
        team_id = _membership_team_id(membership, getattr(obj, "membership_id", None))
        if team_id is None:
            return set()
        return {team_id}

    def _filter_queryset_by_team_ids(
        self, qs: QuerySet, team_ids: Iterable[int]
    ) -> QuerySet:
        return qs.filter(membership__team_id__in=list(team_ids))


@admin.register(TaskAssignment)
class TaskAssignmentAdmin(TeamScopedAdmin):
    add_permission_key = "assign_task_all"
    change_permission_key = "assign_task_all"
    delete_permission_key = "assign_task_all"
    team_permission_key = "assign_task"

    list_display = ("membership", "task", "assigned_by", "assigned_at")
    list_filter = ("membership__team",)
    search_fields = (
        "membership__team__name",
        "membership__user__username",
        "task__id",
    )
    readonly_fields = ("assigned_at",)

    def formfield_for_foreignkey(self, db_field, request, **kwargs):
        is_superuser = getattr(request.user, "is_superuser", False)
        if db_field.name == "membership" and not is_superuser:
            allowed_ids = _get_team_ids_for_user(request.user, self.team_permission_key)
            kwargs["queryset"] = (
                TeamMember.objects.filter(team_id__in=list(allowed_ids), is_active=True)
                if allowed_ids
                else TeamMember.objects.none()
            )
        if db_field.name == "assigned_by" and not is_superuser:
            kwargs["queryset"] = type(request.user).objects.filter(pk=request.user.pk)
            kwargs["initial"] = request.user.pk
        return super().formfield_for_foreignkey(db_field, request, **kwargs)

    def get_object_team_ids(self, obj) -> Set[int]:
        membership = getattr(obj, "membership", None)
        team_id = _membership_team_id(membership, getattr(obj, "membership_id", None))
        if team_id is None:
            return set()
        return {team_id}

    def _filter_queryset_by_team_ids(
        self, qs: QuerySet, team_ids: Iterable[int]
    ) -> QuerySet:
        return qs.filter(membership__team_id__in=list(team_ids))
