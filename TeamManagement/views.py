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

from .models import Role, Team, TeamMember

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
    users = User.objects.all().order_by("-date_joined")
    return render(
        request, "TeamManagement/team_list.html", {"teams": teams, "users": users}
    )


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
            if ROLE_FIELD_NAME and ROLE_FIELD_NAME in TEAM_MEMBER_FIELDS:
                # Try to get a default manager role
                default_role = getattr(TeamMember, "DEFAULT_MANAGER_ROLE", None)
                if default_role is None:
                    # Try to find a role with manager-like name
                    for role_hint in MANAGER_ROLE_HINTS:
                        default_role = Role.objects.filter(
                            name__iexact=role_hint
                        ).first()
                        if default_role:
                            break
                    # If still no role found, get or create a default manager role
                    if default_role is None:
                        default_role, _ = Role.objects.get_or_create(
                            name="Manager",
                            defaults={
                                "description": "Team manager with full permissions"
                            },
                        )
                membership_defaults[ROLE_FIELD_NAME] = default_role
            TeamMember.objects.get_or_create(
                **{TEAM_FIELD_NAME: team, USER_FIELD_NAME: request.user},
                defaults=membership_defaults,
            )
        messages.success(request, ("Team created successfully"))
        return redirect(_safe_reverse("team-detail", pk=team.pk))
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
        return redirect(_safe_reverse("team-detail", pk=team.pk))
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
    return redirect(_safe_reverse("team-list"))


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
        messages.success(request, _("Member added successfully"))
        return redirect(_safe_reverse("team-detail", pk=team.pk))
    return render(
        request, "TeamManagement/team_member_form.html", {"form": form, "team": team}
    )


@login_required
@require_http_methods(["GET", "POST"])
def team_member_update(request, pk, member_id):
    """编辑团队成员"""
    team = get_object_or_404(Team, pk=pk)
    _ensure_team_permission(request.user, team, manage=True)
    membership = get_object_or_404(
        TeamMember.objects.select_related(*SELECT_RELATED_FIELDS),
        pk=member_id,
        **{TEAM_FIELD_NAME: team},
    )

    form = TeamMemberForm(request.POST or None, instance=membership, team=team)
    if request.method == "POST" and form.is_valid():
        form.save()
        messages.success(request, _("Member updated successfully"))
        return redirect("TeamManagement:team-member-list", pk=team.pk)

    return render(
        request,
        "TeamManagement/team_member_form.html",
        {"form": form, "team": team, "member": membership, "action": "update"},
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
    return redirect(_safe_reverse("team-detail", pk=team.pk))


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
        # User does not have management permissions; can_manage remains False.
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


# 用户管理视图
class UserCreationForm(forms.ModelForm):
    password1 = forms.CharField(
        label="密码", widget=forms.PasswordInput(attrs={"class": "form-control"})
    )
    password2 = forms.CharField(
        label="确认密码", widget=forms.PasswordInput(attrs={"class": "form-control"})
    )

    class Meta:
        model = User
        fields = ("username", "email", "first_name", "last_name")
        widgets = {
            "username": forms.TextInput(attrs={"class": "form-control"}),
            "email": forms.EmailInput(attrs={"class": "form-control"}),
            "first_name": forms.TextInput(attrs={"class": "form-control"}),
            "last_name": forms.TextInput(attrs={"class": "form-control"}),
        }

    def clean_password2(self):
        password1 = self.cleaned_data.get("password1")
        password2 = self.cleaned_data.get("password2")
        if password1 and password2 and password1 != password2:
            raise forms.ValidationError("两次输入的密码不一致")
        return password2

    def save(self, commit=True):
        user = super().save(commit=False)
        user.set_password(self.cleaned_data["password1"])
        user.is_active = True  # 确保新用户默认激活
        user.is_staff = True  # 允许用户登录系统（Django Admin要求）
        if commit:
            user.save()
        return user


class UserUpdateForm(forms.ModelForm):
    is_staff = forms.BooleanField(
        label="职员状态",
        required=False,
        help_text="允许用户访问管理后台",
        widget=forms.CheckboxInput(attrs={"class": "form-check-input"}),
    )
    is_superuser = forms.BooleanField(
        label="超级用户状态",
        required=False,
        help_text="拥有所有权限，无需显式分配",
        widget=forms.CheckboxInput(attrs={"class": "form-check-input"}),
    )

    class Meta:
        model = User
        fields = (
            "username",
            "email",
            "first_name",
            "last_name",
            "is_active",
            "is_staff",
            "is_superuser",
        )
        widgets = {
            "username": forms.TextInput(attrs={"class": "form-control"}),
            "email": forms.EmailInput(attrs={"class": "form-control"}),
            "first_name": forms.TextInput(attrs={"class": "form-control"}),
            "last_name": forms.TextInput(attrs={"class": "form-control"}),
        }


@login_required
@require_http_methods(["GET", "POST"])
def user_create(request):
    """创建新用户"""
    if not request.user.is_superuser:
        raise PermissionDenied("只有管理员可以创建用户")

    form = UserCreationForm(request.POST or None)
    if request.method == "POST" and form.is_valid():
        form.save()
        messages.success(request, _("用户创建成功"))
        return redirect("TeamManagement:team-list")
    return render(
        request, "TeamManagement/user_form.html", {"form": form, "action": "create"}
    )


@login_required
@require_http_methods(["GET", "POST"])
def user_update(request, user_id):
    """更新用户信息"""
    if not request.user.is_superuser:
        raise PermissionDenied("只有管理员可以编辑用户")

    user = get_object_or_404(User, pk=user_id)
    form = UserUpdateForm(request.POST or None, instance=user)
    if request.method == "POST" and form.is_valid():
        form.save()
        messages.success(request, _("用户信息已更新"))
        return redirect("TeamManagement:team-list")
    return render(
        request,
        "TeamManagement/user_form.html",
        {"form": form, "action": "update", "edited_user": user},
    )


@login_required
@require_http_methods(["POST"])
def user_delete(request, user_id):
    """删除用户"""
    if not request.user.is_superuser:
        raise PermissionDenied("只有管理员可以删除用户")

    user = get_object_or_404(User, pk=user_id)
    if user == request.user:
        messages.error(request, _("不能删除自己的账号"))
        return redirect("TeamManagement:team-list")

    username = user.get_username()
    user.delete()
    messages.success(request, _(f"用户 {username} 已被删除"))
    return redirect("TeamManagement:team-list")


@login_required
@require_http_methods(["GET", "POST"])
def user_change_password(request, user_id):
    """修改用户密码"""
    if not request.user.is_superuser:
        raise PermissionDenied("只有管理员可以修改用户密码")

    user = get_object_or_404(User, pk=user_id)

    if request.method == "POST":
        password1 = request.POST.get("password1")
        password2 = request.POST.get("password2")

        if password1 and password2:
            if password1 == password2:
                user.set_password(password1)
                user.save()
                messages.success(request, _(f"用户 {user.get_username()} 的密码已更新"))
                return redirect("TeamManagement:team-list")
            else:
                messages.error(request, _("两次输入的密码不一致"))
        else:
            messages.error(request, _("请输入密码"))

    return render(
        request, "TeamManagement/user_password_form.html", {"edited_user": user}
    )
