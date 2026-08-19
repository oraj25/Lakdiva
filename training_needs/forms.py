from django import forms

from django.utils import timezone


# =========================================================
# ADDITIONAL TRAINING ASSIGNMENT
# =========================================================

class AdditionalTrainingAssignmentForm(
    forms.Form
):

    due_date = forms.DateField(
        required=False,
        label="Due Date",
        widget=forms.DateInput(
            attrs={
                "class": "form-control",
                "type": "date",
            }
        ),
    )


    def clean_due_date(self):

        due_date = (
            self.cleaned_data.get(
                "due_date"
            )
        )

        if (
            due_date
            and
            due_date
            < timezone.localdate()
        ):

            raise forms.ValidationError(
                (
                    "Due date cannot be "
                    "in the past."
                )
            )

        return due_date