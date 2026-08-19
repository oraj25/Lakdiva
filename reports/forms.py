from django import forms


# =========================================================
# SECURITY REPORT FILTER
# =========================================================

class SecurityReportFilterForm(
    forms.Form
):

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
            and date_to
            and date_from > date_to
        ):

            raise forms.ValidationError(
                (
                    "The From date cannot "
                    "be after the To date."
                )
            )

        return cleaned_data