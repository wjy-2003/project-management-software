from django import forms
from django.core.exceptions import ValidationError
from django.utils.translation import gettext_lazy as _
from models import Team, TeamMembership

class TeamForm(forms.ModelForm):
    class Meta:
        model = Team
        fields = ("name", "description")
        widgets = {
            "name": forms.TextInput(attrs={"placeholder": _("Team name")}),
            "description": forms.Textarea(attrs={"rows": 4, "placeholder": _("Short description")}),
        }

    def __init__(self, *args, owner=None, **kwargs):
        self.owner = owner
        super().__init__(*args, **kwargs)

    def clean_name(self):
        name = self.cleaned_data["name"]
        if (
            self.owner
            and Team.objects.filter(owner=self.owner, name__iexact=name)
            .exclude(pk=self.instance.pk if self.instance else None)
            .exists()
        ):
            raise ValidationError(_("You already have a team with this name."))
        return name


class TeamMembershipForm(forms.ModelForm):
    class Meta:
        model = TeamMembership
        fields = ("role", "is_active")

    def __init__(self, *args, team=None, **kwargs):
        self.team = team
        super().__init__(*args, **kwargs)

    def clean(self):
        cleaned_data = super().clean()
        if not self.instance.pk and not self.team:
            raise ValidationError(_("Team context is required to add a membership."))
        return cleaned_data
