from django import forms
from django.contrib.auth import get_user_model

from .models import Role, Team, TeamMember

User = get_user_model()


class TeamForm(forms.ModelForm):
    """
    Form for creating and updating a Team.
    The 'owner' field is automatically set to the current user in the view.
    """

    class Meta:
        model = Team
        fields = ["name", "description"]


class TeamMemberForm(forms.ModelForm):
    """
    Form for adding a new member to a Team.
    """

    class Meta:
        model = TeamMember
        fields = ["user", "role", "is_active"]

    def __init__(self, *args, team: Team | None = None, **kwargs):
        """
        - Excludes users who are already members of the specified team.
        - Sets a default 'is_active' value.
        """
        super().__init__(*args, **kwargs)
        self.fields["is_active"].initial = True

        if team:
            # Get IDs of users already in the team
            existing_user_ids = team.members.values_list("user_id", flat=True)
            # Exclude existing users from the 'user' field queryset
            self.fields["user"].queryset = User.objects.exclude(
                id__in=existing_user_ids
            )

        # Ensure the 'role' queryset is not empty
        if not Role.objects.exists():
            self.fields["role"].queryset = Role.objects.none()
            self.fields["role"].help_text = (
                "No roles available. Please create roles in the admin panel."
            )
