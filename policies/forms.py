import re

from django import forms

from .models import Policy


# =========================================================
# POLICY FORM
# =========================================================

class PolicyForm(forms.ModelForm):

    class Meta:

        model = Policy

        fields = [
            "title",
            "policy_type",
            "version",
            "content",
            "effective_date",
            "review_date",
        ]

        widgets = {

            "title": forms.TextInput(
                attrs={
                    "class": "form-control",
                    "placeholder": (
                        "Example: POS Security Policy"
                    ),
                }
            ),

            "policy_type": forms.Select(
                attrs={
                    "class": "form-control",
                }
            ),

            "version": forms.TextInput(
                attrs={
                    "class": "form-control",
                    "placeholder": "Example: 1.0",
                }
            ),

            "content": forms.Textarea(
                attrs={
                    "class": "form-control",
                    "rows": 16,
                    "placeholder": (
                        "Enter the security "
                        "policy content..."
                    ),
                }
            ),

            "effective_date": forms.DateInput(
                attrs={
                    "class": "form-control",
                    "type": "date",
                }
            ),

            "review_date": forms.DateInput(
                attrs={
                    "class": "form-control",
                    "type": "date",
                }
            ),
        }

    # -----------------------------------------------------
    # TITLE
    # -----------------------------------------------------

    def clean_title(self):

        title = self.cleaned_data[
            "title"
        ].strip()

        if len(title) < 3:

            raise forms.ValidationError(
                "Policy title is too short."
            )

        return title

    # -----------------------------------------------------
    # VERSION
    # -----------------------------------------------------

    def clean_version(self):

        version = self.cleaned_data[
            "version"
        ].strip()

        if not re.fullmatch(
            r"\d+(\.\d+){0,2}",
            version,
        ):

            raise forms.ValidationError(
                (
                    "Use a version such as "
                    "1.0, 1.1 or 2.0."
                )
            )

        return version

    # -----------------------------------------------------
    # DATES
    # -----------------------------------------------------

    def clean(self):

        cleaned_data = super().clean()

        effective_date = (
            cleaned_data.get(
                "effective_date"
            )
        )

        review_date = (
            cleaned_data.get(
                "review_date"
            )
        )

        if (
            effective_date
            and review_date
            and review_date < effective_date
        ):

            self.add_error(
                "review_date",
                (
                    "Review date cannot be "
                    "before the effective date."
                ),
            )

        return cleaned_data


# =========================================================
# NEW VERSION FORM
# =========================================================

class NewPolicyVersionForm(forms.Form):

    version = forms.CharField(
        max_length=20,
        label="New Version",
        widget=forms.TextInput(
            attrs={
                "class": "form-control",
                "placeholder": "Example: 1.1",
            }
        ),
    )

    def clean_version(self):

        version = (
            self.cleaned_data[
                "version"
            ].strip()
        )

        if not re.fullmatch(
            r"\d+(\.\d+){0,2}",
            version,
        ):

            raise forms.ValidationError(
                (
                    "Use a version such as "
                    "1.1 or 2.0."
                )
            )

        return version