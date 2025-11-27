from django import forms
from django.contrib import messages
from django.contrib.auth import get_user_model
from django.contrib.auth.decorators import login_required
from django.core.exceptions import ImproperlyConfigured, PermissionDenied
from django.db import transaction
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import NoReverseMatch, reverse
from django.utils.translation import gettext_lazy as _
from django.views.decorators.http import require_http_methods

from .models import Team, TeamMember

User = get_user_model()
MANAGER_ROLE_HINTS = {"owner", "admin", "manager", "leader", "maintainer", "captain"}

TEAM_MEMBER_FIELDS = {field.name: field for field in TeamMember._meta.fields}
TEAM_FIELD_NAME = next(
    (
        name
        for name, field in TEAM_MEMBER_FIELDS.items()
        if field.is_relation and field.related_model == Team
    ),
    None,
)
USER_FIELD_NAME = next(
    (
        name
        for name, field in TEAM_MEMBER_FIELDS.items()
        if field.is_relation and field.related_model == User
    ),
    None,
)

if TEAM_FIELD_NAME is None or USER_FIELD_NAME is None:
    raise ImproperlyConfigured(
        "TeamMember model must include foreign key fields to both Team and the user model."
    )

TEAM_FIELD_ID_LOOKUP = f"{TEAM_FIELD_NAME}_id"
USER_FIELD_LOOKUP = USER_FIELD_NAME

ROLE_FIELD_NAME = next(
    (
        name
        for name, field in TEAM_MEMBER_FIELDS.items()
        if field.name == "role"
        or (
            field.related_model
            and field.related_model.__name__.lower() in {"role", "teamrole"}
        )
    ),
    None,
)

SELECT_RELATED_FIELDS = [USER_FIELD_NAME]
if ROLE_FIELD_NAME:
    SELECT_RELATED_FIELDS.append(ROLE_FIELD_NAME)


def _safe_reverse(name: str, *args, **kwargs):
    try:
        return reverse(f"TeamManagement:{name}", args=args, kwargs=kwargs)
    except NoReverseMatch:
        return reverse(name, args=args, kwargs=kwargs)


def _membership_can_manage(membership: TeamMember | None) -> bool:
    if membership is None:
        return False
    for flag in ("can_manage", "is_manager", "is_admin"):
        if hasattr(membership, flag):
            return bool(getattr(membership, flag))
    if ROLE_FIELD_NAME:
        role = getattr(membership, ROLE_FIELD_NAME, None)
        if role is None:
            return False
        if hasattr(role, "can_manage"):
            return bool(role.can_manage)
        if hasattr(role, "code"):
            return str(role.code).lower() in MANAGER_ROLE_HINTS
        if isinstance(role, str):
            return role.lower() in MANAGER_ROLE_HINTS
        if hasattr(role, "name"):
            return str(role.name).lower() in MANAGER_ROLE_HINTS
    return False


def _ensure_team_permission(user, team: Team, manage: bool = False):
    if not user.is_authenticated:
        raise PermissionDenied
    if user.is_superuser:
        return
    app_label = Team._meta.app_label
    model = Team._meta.model_name
    perm_codename = f"{app_label}.{'change' if manage else 'view'}_{model}"
    if user.has_perm(perm_codename):
        return
    membership = (
        TeamMember.objects.filter(**{TEAM_FIELD_NAME: team, USER_FIELD_NAME: user})
        .select_related(*SELECT_RELATED_FIELDS)
        .first()
    )
    if membership is None:
        raise PermissionDenied
    if manage and not _membership_can_manage(membership):
        raise PermissionDenied


def _ensure_can_add_team(user):
    if not user.is_authenticated:
        raise PermissionDenied
    if user.is_superuser:
        return
    perm_codename = f"{Team._meta.app_label}.add_{Team._meta.model_name}"
    if not user.has_perm(perm_codename):
        raise PermissionDenied


def _visible_teams(user):
    if not user.is_authenticated:
        return Team.objects.none()
    qs = Team.objects.all()
    perm_codename = f"{Team._meta.app_label}.view_{Team._meta.model_name}"
    if user.is_superuser or user.has_perm(perm_codename):
        return qs
    team_ids = TeamMember.objects.filter(**{USER_FIELD_NAME: user}).values_list(
        TEAM_FIELD_ID_LOOKUP, flat=True
    )
    return qs.filter(pk__in=team_ids)


class TeamForm(forms.ModelForm):
    class Meta:
        model = Team
        fields = [
            field.name
            for field in Team._meta.fields
            if field.editable and not field.auto_created
        ]


class TeamMemberForm(forms.ModelForm):
    class Meta:
        model = TeamMember
        exclude = [
            field.name
            for field in TeamMember._meta.fields
            if field.auto_created or not field.editable or field.name == TEAM_FIELD_NAME
        ]

    def __init__(self, *args, team: Team | None = None, **kwargs):
        super().__init__(*args, **kwargs)
        if team and USER_FIELD_NAME in self.fields:
            current_members = TeamMember.objects.filter(
                **{TEAM_FIELD_NAME: team}
            ).values_list(f"{USER_FIELD_NAME}_id", flat=True)
            self.fields[USER_FIELD_NAME].queryset = User.objects.exclude(
                pk__in=current_members
            )


@login_required
def team_list(request):
    teams = _visible_teams(request.user)
    return render(request, "TeamManagement/team_list.html", {"teams": teams})


@login_required
def team_detail(request, pk):
    team = get_object_or_404(Team, pk=pk)
    _ensure_team_permission(request.user, team, manage=False)
    members = TeamMember.objects.filter(**{TEAM_FIELD_NAME: team}).select_related(
        *SELECT_RELATED_FIELDS
    )
    return render(
        request, "TeamManagement/team_detail.html", {"team": team, "members": members}
    )


@login_required
@require_http_methods(["GET", "POST"])
def team_create(request):
    _ensure_can_add_team(request.user)
    form = TeamForm(request.POST or None)
    if request.method == "POST" and form.is_valid():
        with transaction.atomic():
            team = form.save()
            membership_defaults = {}
            for flag in ("is_manager", "can_manage", "is_admin"):
                if flag in TEAM_MEMBER_FIELDS:
                    membership_defaults[flag] = True
            if ROLE_FIELD_NAME and ROLE_FIELD_NAME in TeamMemberForm.Meta.fields:
                default_role = getattr(TeamMember, "DEFAULT_MANAGER_ROLE", None)
                if default_role is not None:
                    membership_defaults[ROLE_FIELD_NAME] = default_role
            TeamMember.objects.get_or_create(
                **{TEAM_FIELD_NAME: team, USER_FIELD_NAME: request.user},
                defaults=membership_defaults,
            )
        messages.success(request, _("Team created successfully"))
        return redirect(_safe_reverse("team_detail", pk=team.pk))
    return render(request, "TeamManagement/team_form.html", {"form": form})


@login_required
@require_http_methods(["GET", "POST"])
def team_update(request, pk):
    team = get_object_or_404(Team, pk=pk)
    _ensure_team_permission(request.user, team, manage=True)
    form = TeamForm(request.POST or None, instance=team)
    if request.method == "POST" and form.is_valid():
        form.save()
        messages.success(request, _("Team information updated successfully"))
        return redirect(_safe_reverse("team_detail", pk=team.pk))
    return render(
        request, "TeamManagement/team_form.html", {"form": form, "team": team}
    )


@login_required
@require_http_methods(["POST"])
def team_delete(request, pk):
    team = get_object_or_404(Team, pk=pk)
    _ensure_team_permission(request.user, team, manage=True)
    team.delete()
    messages.success(request, _("Team deleted successfully"))
    return redirect(_safe_reverse("team_list"))


@login_required
@require_http_methods(["GET", "POST"])
def team_member_add(request, pk):
    team = get_object_or_404(Team, pk=pk)
    _ensure_team_permission(request.user, team, manage=True)
    form = TeamMemberForm(request.POST or None, team=team)
    if request.method == "POST" and form.is_valid():
        membership = form.save(commit=False)
        setattr(membership, TEAM_FIELD_NAME, team)
        membership.save()
        messages.success(request, _("Member added to team successfully"))
        return redirect(_safe_reverse("team_detail", pk=team.pk))
    return render(
        request, "TeamManagement/team_member_form.html", {"form": form, "team": team}
    )


@login_required
@require_http_methods(["POST"])
def team_member_remove(request, pk, member_id):
    team = get_object_or_404(Team, pk=pk)
    _ensure_team_permission(request.user, team, manage=True)
    membership = get_object_or_404(
        TeamMember.objects.select_related(*SELECT_RELATED_FIELDS),
        pk=member_id,
        **{TEAM_FIELD_NAME: team},
    )
    if (
        getattr(membership, USER_FIELD_NAME) == request.user
        and not request.user.is_superuser
    ):
        raise PermissionDenied(_("Cannot remove yourself."))
    membership.delete()
    messages.success(request, _("Member removed successfully"))
    return redirect(_safe_reverse("team_detail", pk=team.pk))


@login_required
def team_member_list(request, pk):
    """显示团队成员列表"""
    team = get_object_or_404(Team, pk=pk)
    _ensure_team_permission(request.user, team, manage=False)
    members = TeamMember.objects.filter(**{TEAM_FIELD_NAME: team}).select_related(
        *SELECT_RELATED_FIELDS
    )

    # 检查当前用户是否可以管理团队
    can_manage = False
    try:
        _ensure_team_permission(request.user, team, manage=True)
        can_manage = True
    except PermissionDenied:
        pass

    return render(
        request,
        "TeamManagement/team_member_list.html",
        {
            "team": team,
            "members": members,
            "can_manage": can_manage,
        },
    )
