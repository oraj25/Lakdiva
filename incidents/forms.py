from pathlib import Path

from django import forms

from django.core.exceptions import (
    ValidationError,
)

from django.utils import timezone

from pos_security.models import (
    POSTerminal,
    POSShift,
)

from .models import (
    Incident,
    IncidentCategory,
    IncidentRiskAssessment,
)


# =========================================================
# EVIDENCE VALIDATION
# =========================================================

ALLOWED_EVIDENCE_EXTENSIONS = {
    ".jpg",
    ".jpeg",
    ".png",
    ".pdf",
    ".txt",
    ".log",
}

MAX_EVIDENCE_SIZE = (
    5 * 1024 * 1024
)


def validate_evidence_file(file):

    extension = (
        Path(
            file.name
        )
        .suffix
        .lower()
    )

    if (
        extension
        not in ALLOWED_EVIDENCE_EXTENSIONS
    ):

        raise ValidationError(
            (
                "Unsupported evidence file. "
                "Allowed types: JPG, JPEG, "
                "PNG, PDF, TXT and LOG."
            )
        )

    if file.size > MAX_EVIDENCE_SIZE:

        raise ValidationError(
            (
                "Each evidence file must "
                "be 5 MB or smaller."
            )
        )

    if file.size <= 0:

        raise ValidationError(
            "Evidence file is empty."
        )


# =========================================================
# MULTIPLE FILE INPUT
# =========================================================

class MultipleFileInput(
    forms.ClearableFileInput
):

    allow_multiple_selected = True


class MultipleFileField(
    forms.FileField
):

    def __init__(
        self,
        *args,
        **kwargs,
    ):

        kwargs.setdefault(
            "widget",
            MultipleFileInput(
                attrs={
                    "accept": (
                        ".jpg,.jpeg,.png,"
                        ".pdf,.txt,.log"
                    )
                }
            ),
        )

        super().__init__(
            *args,
            **kwargs
        )

    def clean(
        self,
        data,
        initial=None,
    ):

        if not data:

            return []

        files = (
            data
            if isinstance(
                data,
                (list, tuple),
            )
            else [data]
        )

        cleaned_files = []

        for uploaded_file in files:

            cleaned_file = (
                super().clean(
                    uploaded_file,
                    initial,
                )
            )

            validate_evidence_file(
                cleaned_file
            )

            cleaned_files.append(
                cleaned_file
            )

        return cleaned_files


# =========================================================
# INCIDENT REPORT FORM
# =========================================================

class IncidentReportForm(
    forms.ModelForm
):

    evidence = MultipleFileField(
        required=False,
        label="Supporting Evidence",
    )

    class Meta:

        model = Incident

        fields = [
            "category",
            "title",
            "description",
            "occurred_at",
            "pos",
            "shift",
        ]

        widgets = {

            "category": forms.Select(
                attrs={
                    "class": "form-control",
                }
            ),

            "title": forms.TextInput(
                attrs={
                    "class": "form-control",
                    "placeholder": (
                        "Short incident title"
                    ),
                }
            ),

            "description": (
                forms.Textarea(
                    attrs={
                        "class": "form-control",
                        "rows": 7,
                        "placeholder": (
                            "Describe what "
                            "happened and what "
                            "you observed..."
                        ),
                    }
                )
            ),

            "occurred_at": (
                forms.DateTimeInput(
                    format=(
                        "%Y-%m-%dT%H:%M"
                    ),
                    attrs={
                        "class": (
                            "form-control"
                        ),
                        "type": (
                            "datetime-local"
                        ),
                    },
                )
            ),

            "pos": forms.Select(
                attrs={
                    "class": "form-control",
                }
            ),

            "shift": forms.Select(
                attrs={
                    "class": "form-control",
                }
            ),
        }

    def __init__(
        self,
        *args,
        user=None,
        **kwargs,
    ):

        super().__init__(
            *args,
            **kwargs
        )

        self.user = user

        self.fields[
            "category"
        ].queryset = (
            IncidentCategory.objects
            .filter(
                status=(
                    IncidentCategory
                    .Status
                    .ACTIVE
                )
            )
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

        self.fields[
            "pos"
        ].required = False

        self.fields[
            "shift"
        ].required = False

        if user:

            self.fields[
                "shift"
            ].queryset = (
                POSShift.objects
                .filter(
                    user=user
                )
                .select_related(
                    "pos"
                )
                .order_by(
                    "-shift_start"
                )[:50]
            )

        else:

            self.fields[
                "shift"
            ].queryset = (
                POSShift.objects.none()
            )

    def clean_title(self):

        title = (
            self.cleaned_data[
                "title"
            ].strip()
        )

        if len(title) < 5:

            raise forms.ValidationError(
                (
                    "Incident title must "
                    "contain at least "
                    "5 characters."
                )
            )

        return title

    def clean_description(self):

        description = (
            self.cleaned_data[
                "description"
            ].strip()
        )

        if len(description) < 10:

            raise forms.ValidationError(
                (
                    "Please provide a more "
                    "detailed description."
                )
            )

        return description

    def clean_evidence(self):

        files = (
            self.cleaned_data.get(
                "evidence"
            )
            or []
        )

        if len(files) > 3:

            raise forms.ValidationError(
                (
                    "A maximum of 3 evidence "
                    "files can be uploaded."
                )
            )

        return files

    def clean(self):

        cleaned_data = (
            super().clean()
        )

        occurred_at = (
            cleaned_data.get(
                "occurred_at"
            )
        )

        pos = (
            cleaned_data.get(
                "pos"
            )
        )

        shift = (
            cleaned_data.get(
                "shift"
            )
        )

        if (
            occurred_at
            and occurred_at
            > timezone.now()
        ):

            self.add_error(
                "occurred_at",
                (
                    "Incident time cannot "
                    "be in the future."
                ),
            )

        if shift:

            if (
                self.user
                and shift.user_id
                != self.user.user_id
            ):

                self.add_error(
                    "shift",
                    (
                        "You cannot select "
                        "another employee's "
                        "shift."
                    ),
                )

            if (
                pos
                and shift.pos_id
                != pos.pos_id
            ):

                self.add_error(
                    "pos",
                    (
                        "Selected POS does "
                        "not match the "
                        "selected shift."
                    ),
                )

        return cleaned_data
# =========================================================
# RISK ASSESSMENT FORM
# =========================================================

RISK_YES_NO_CHOICES = (

    (
        "False",
        "No"
    ),

    (
        "True",
        "Yes"
    ),
)


def risk_string_to_bool(
    value,
):

    return value == "True"


class IncidentRiskAssessmentForm(
    forms.ModelForm
):

    customer_data_involved = (
        forms.TypedChoiceField(
            choices=(
                RISK_YES_NO_CHOICES
            ),
            coerce=risk_string_to_bool,
            widget=forms.RadioSelect,
            label=(
                "Is customer or sensitive "
                "data involved?"
            ),
        )
    )

    pos_affected = (
        forms.TypedChoiceField(
            choices=(
                RISK_YES_NO_CHOICES
            ),
            coerce=risk_string_to_bool,
            widget=forms.RadioSelect,
            label=(
                "Is a POS terminal affected?"
            ),
        )
    )

    unauthorized_access = (
        forms.TypedChoiceField(
            choices=(
                RISK_YES_NO_CHOICES
            ),
            coerce=risk_string_to_bool,
            widget=forms.RadioSelect,
            label=(
                "Is unauthorized access "
                "suspected or involved?"
            ),
        )
    )

    business_impact = (
        forms.TypedChoiceField(
            choices=(
                (
                    0,
                    (
                        "No significant business "
                        "operation impact (+0)"
                    ),
                ),

                (
                    2,
                    (
                        "Business operations "
                        "affected (+2)"
                    ),
                ),
            ),
            coerce=int,
            widget=forms.RadioSelect,
            label=(
                "Were business operations "
                "affected?"
            ),
        )
    )


    class Meta:

        model = (
            IncidentRiskAssessment
        )

        fields = [
            "customer_data_involved",
            "pos_affected",
            "unauthorized_access",
            "business_impact",
        ]


# =========================================================
# INCIDENT INVESTIGATION / RESOLUTION FORM
# =========================================================

class IncidentActionForm(forms.Form):

    action_type = forms.ChoiceField(
        choices=[
            (
                "INVESTIGATION",
                "Investigation",
            ),
            (
                "CORRECTIVE_ACTION",
                "Corrective Action",
            ),
            (
                "RESOLUTION",
                "Resolution",
            ),
        ],
        widget=forms.Select,
        label="Action Type",
    )

    notes = forms.CharField(
        widget=forms.Textarea(
            attrs={
                "rows": 6,
                "placeholder": (
                    "Enter investigation findings, "
                    "corrective action, or resolution "
                    "details..."
                ),
            }
        ),
        min_length=10,
        max_length=5000,
        label="Details",
    )