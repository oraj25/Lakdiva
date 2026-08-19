from django import forms

from accounts.models import (
    User,
)

from .models import (
    AuditLog,
)


# =========================================================
# AUDIT LOG FILTER FORM
# =========================================================

class AuditLogFilterForm(
    forms.Form
):

    search = forms.CharField(
        required=False,
        label="Search",
        widget=forms.TextInput(
            attrs={
                "class": "form-control",
                "placeholder": (
                    "User, action, entity, "
                    "details or IP..."
                ),
            }
        ),
    )

    user = forms.ModelChoiceField(
        required=False,
        queryset=User.objects.none(),
        empty_label="All Users",
        widget=forms.Select(
            attrs={
                "class": "form-control",
            }
        ),
    )

    action = forms.ChoiceField(
        required=False,
        choices=[
            (
                "",
                "All Actions",
            )
        ],
        widget=forms.Select(
            attrs={
                "class": "form-control",
            }
        ),
    )

    entity_type = forms.ChoiceField(
        required=False,
        choices=[
            (
                "",
                "All Entities",
            )
        ],
        widget=forms.Select(
            attrs={
                "class": "form-control",
            }
        ),
    )

    date_from = forms.DateField(
        required=False,
        label="From",
        widget=forms.DateInput(
            attrs={
                "class": "form-control",
                "type": "date",
            }
        ),
    )

    date_to = forms.DateField(
        required=False,
        label="To",
        widget=forms.DateInput(
            attrs={
                "class": "form-control",
                "type": "date",
            }
        ),
    )


    # -----------------------------------------------------
    # INITIALIZE FILTER OPTIONS
    # -----------------------------------------------------

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
            "user"
        ].queryset = (
            User.objects
            .order_by(
                "staff_no"
            )
        )


        action_values = (
            AuditLog.objects
            .exclude(
                action=""
            )
            .order_by(
                "action"
            )
            .values_list(
                "action",
                flat=True,
            )
            .distinct()
        )


        self.fields[
            "action"
        ].choices = [

            (
                "",
                "All Actions",
            ),

            *[
                (
                    value,
                    value,
                )

                for value
                in action_values
            ],
        ]


        entity_values = (
            AuditLog.objects
            .exclude(
                entity_type=""
            )
            .order_by(
                "entity_type"
            )
            .values_list(
                "entity_type",
                flat=True,
            )
            .distinct()
        )


        self.fields[
            "entity_type"
        ].choices = [

            (
                "",
                "All Entities",
            ),

            *[
                (
                    value,
                    value,
                )

                for value
                in entity_values
            ],
        ]


    # -----------------------------------------------------
    # VALIDATE DATE RANGE
    # -----------------------------------------------------

    def clean(self):

        cleaned_data = (
            super().clean()
        )

        date_from = (
            cleaned_data.get(
                "date_from"
            )
        )

        date_to = (
            cleaned_data.get(
                "date_to"
            )
        )

        if (
            date_from
            and
            date_to
            and
            date_from > date_to
        ):

            raise forms.ValidationError(
                (
                    "The From date cannot "
                    "be after the To date."
                )
            )

        return cleaned_data