from django import forms

from accounts.models import (
    Role,
    User,
)

from .models import (
    DailySecurityCheck,
    POSTerminal,
    POSShift,
)


# =========================================================
# START SHIFT
# =========================================================

class StartShiftForm(forms.ModelForm):

    class Meta:

        model = POSShift

        fields = [
            "pos",
            "opening_cash",
        ]

        widgets = {

            "pos": forms.Select(
                attrs={
                    "class": "form-control",
                }
            ),

            "opening_cash": (
                forms.NumberInput(
                    attrs={
                        "class": "form-control",
                        "min": "0",
                        "step": "0.01",
                        "placeholder": (
                            "Opening cash"
                        ),
                    }
                )
            ),
        }

    def __init__(
        self,
        *args,
        **kwargs,
    ):

        super().__init__(
            *args,
            **kwargs
        )

        self.fields[
            "pos"
        ].queryset = (
            POSTerminal.objects.filter(
                status=(
                    POSTerminal
                    .Status
                    .ACTIVE
                )
            )
        )


# =========================================================
# UPDATE CASH TOTALS
# =========================================================

class CashUpdateForm(forms.ModelForm):

    class Meta:

        model = POSShift

        fields = [
            "cash_in",
            "cash_out",
        ]

        widgets = {

            "cash_in": forms.NumberInput(
                attrs={
                    "class": "form-control",
                    "min": "0",
                    "step": "0.01",
                }
            ),

            "cash_out": forms.NumberInput(
                attrs={
                    "class": "form-control",
                    "min": "0",
                    "step": "0.01",
                }
            ),
        }


# =========================================================
# SECURITY CHECK
# =========================================================

YES_NO_CHOICES = (
    ("False", "No"),
    ("True", "Yes"),
)


def string_to_bool(value):

    return value == "True"


class DailySecurityCheckForm(
    forms.ModelForm
):

    is_unknown_device_present = (
        forms.TypedChoiceField(
            choices=YES_NO_CHOICES,
            coerce=string_to_bool,
            widget=forms.RadioSelect,
            label=(
                "Is there an unknown or "
                "unauthorized device connected "
                "to the POS?"
            ),
        )
    )

    is_unusual_behavior_observed = (
        forms.TypedChoiceField(
            choices=YES_NO_CHOICES,
            coerce=string_to_bool,
            widget=forms.RadioSelect,
            label=(
                "Is the POS behaving unusually?"
            ),
        )
    )

    is_physically_secure = (
        forms.TypedChoiceField(
            choices=YES_NO_CHOICES,
            coerce=string_to_bool,
            widget=forms.RadioSelect,
            label=(
                "Is the POS terminal "
                "physically secure?"
            ),
        )
    )

    is_credentials_secure = (
        forms.TypedChoiceField(
            choices=YES_NO_CHOICES,
            coerce=string_to_bool,
            widget=forms.RadioSelect,
            label=(
                "Are POS credentials being "
                "kept secure?"
            ),
        )
    )

    is_suspicious_surroundings = (
        forms.TypedChoiceField(
            choices=YES_NO_CHOICES,
            coerce=string_to_bool,
            widget=forms.RadioSelect,
            label=(
                "Is there suspicious activity "
                "around the POS?"
            ),
        )
    )

    class Meta:

        model = DailySecurityCheck

        fields = [
            "is_unknown_device_present",
            "is_unusual_behavior_observed",
            "is_physically_secure",
            "is_credentials_secure",
            "is_suspicious_surroundings",
            "comments",
        ]

        widgets = {

            "comments": forms.Textarea(
                attrs={
                    "class": "form-control",
                    "rows": 5,
                    "placeholder": (
                        "Optional security "
                        "observations..."
                    ),
                }
            ),
        }


# =========================================================
# CLOSE SHIFT / HANDOVER
# =========================================================

class CloseShiftForm(forms.ModelForm):

    class Meta:

        model = POSShift

        fields = [
            "closing_cash",
            "handed_over_to",
            "handover_notes",
        ]

        widgets = {

            "closing_cash": (
                forms.NumberInput(
                    attrs={
                        "class": "form-control",
                        "min": "0",
                        "step": "0.01",
                    }
                )
            ),

            "handed_over_to": (
                forms.Select(
                    attrs={
                        "class": "form-control",
                    }
                )
            ),

            "handover_notes": (
                forms.Textarea(
                    attrs={
                        "class": "form-control",
                        "rows": 4,
                        "placeholder": (
                            "Optional shift "
                            "handover notes..."
                        ),
                    }
                )
            ),
        }

    def __init__(
        self,
        *args,
        current_user=None,
        **kwargs,
    ):

        super().__init__(
            *args,
            **kwargs
        )

        employees = User.objects.filter(
            role__role_name=(
                Role.EMPLOYEE
            ),
            status=(
                User.Status.ACTIVE
            ),
        )

        if current_user:

            employees = (
                employees.exclude(
                    user_id=(
                        current_user.user_id
                    )
                )
            )

        self.fields[
            "handed_over_to"
        ].queryset = employees

        self.fields[
            "handed_over_to"
        ].required = False