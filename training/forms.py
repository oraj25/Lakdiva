from django import forms
from django.utils import timezone

from accounts.models import (
    Role,
    User,
)

from .models import (
    QuizQuestion,
    TrainingModule,
)


# =========================================================
# TRAINING MODULE FORM
# =========================================================

class TrainingModuleForm(forms.ModelForm):

    class Meta:

        model = TrainingModule

        fields = [
            "title",
            "topic",
            "description",
            "content",
        ]

        widgets = {

            "title": forms.TextInput(
                attrs={
                    "class": "form-control",
                    "placeholder": (
                        "Example: POS Security Awareness"
                    ),
                }
            ),

            "topic": forms.Select(
                attrs={
                    "class": "form-control",
                }
            ),

            "description": forms.Textarea(
                attrs={
                    "class": "form-control",
                    "rows": 4,
                    "placeholder": (
                        "Short description of "
                        "this training module..."
                    ),
                }
            ),

            "content": forms.Textarea(
                attrs={
                    "class": "form-control",
                    "rows": 18,
                    "placeholder": (
                        "Enter the full training "
                        "material here..."
                    ),
                }
            ),
        }

    def clean_title(self):

        title = (
            self.cleaned_data[
                "title"
            ].strip()
        )

        if len(title) < 3:

            raise forms.ValidationError(
                "Training title is too short."
            )

        return title

    def clean_content(self):

        content = (
            self.cleaned_data[
                "content"
            ].strip()
        )

        if len(content) < 20:

            raise forms.ValidationError(
                (
                    "Training content must contain "
                    "at least 20 characters."
                )
            )

        return content


# =========================================================
# TRAINING ASSIGNMENT FORM
# =========================================================

class TrainingAssignmentForm(forms.Form):

    assign_to_all = forms.BooleanField(
        required=False,
        label="Assign to all active employees",
    )

    employees = forms.ModelMultipleChoiceField(
        queryset=User.objects.none(),
        required=False,
        widget=forms.CheckboxSelectMultiple,
        label="Select Employees",
    )

    due_date = forms.DateField(
        required=False,
        widget=forms.DateInput(
            attrs={
                "class": "form-control",
                "type": "date",
            }
        ),
        label="Due Date",
    )

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
            "employees"
        ].queryset = (
            User.objects
            .filter(
                role__role_name=(
                    Role.EMPLOYEE
                ),
                status=User.Status.ACTIVE,
            )
            .order_by(
                "staff_no"
            )
        )

    def clean_due_date(self):

        due_date = (
            self.cleaned_data.get(
                "due_date"
            )
        )

        if (
            due_date
            and due_date
            < timezone.localdate()
        ):

            raise forms.ValidationError(
                (
                    "Due date cannot be "
                    "in the past."
                )
            )

        return due_date

    def clean(self):

        cleaned_data = (
            super().clean()
        )

        assign_to_all = (
            cleaned_data.get(
                "assign_to_all"
            )
        )

        employees = (
            cleaned_data.get(
                "employees"
            )
        )

        if (
            not assign_to_all
            and not employees
        ):

            raise forms.ValidationError(
                (
                    "Select at least one employee "
                    "or select 'Assign to all "
                    "active employees'."
                )
            )

        return cleaned_data


# =========================================================
# QUIZ QUESTION FORM
# =========================================================

class QuizQuestionForm(forms.ModelForm):

    class Meta:

        model = QuizQuestion

        fields = [
            "question_text",
            "option_a",
            "option_b",
            "option_c",
            "option_d",
            "correct_option",
            "marks",
        ]

        widgets = {

            "question_text": forms.Textarea(
                attrs={
                    "class": "form-control",
                    "rows": 4,
                    "placeholder": (
                        "Enter the quiz question..."
                    ),
                }
            ),

            "option_a": forms.TextInput(
                attrs={
                    "class": "form-control",
                    "placeholder": "Option A",
                }
            ),

            "option_b": forms.TextInput(
                attrs={
                    "class": "form-control",
                    "placeholder": "Option B",
                }
            ),

            "option_c": forms.TextInput(
                attrs={
                    "class": "form-control",
                    "placeholder": (
                        "Option C (optional)"
                    ),
                }
            ),

            "option_d": forms.TextInput(
                attrs={
                    "class": "form-control",
                    "placeholder": (
                        "Option D (optional)"
                    ),
                }
            ),

            "correct_option": forms.Select(
                attrs={
                    "class": "form-control",
                }
            ),

            "marks": forms.NumberInput(
                attrs={
                    "class": "form-control",
                    "min": "1",
                }
            ),
        }

    def clean_question_text(self):

        question_text = (
            self.cleaned_data[
                "question_text"
            ].strip()
        )

        if len(question_text) < 5:

            raise forms.ValidationError(
                (
                    "Question must contain "
                    "at least 5 characters."
                )
            )

        return question_text

    def clean(self):

        cleaned_data = super().clean()

        correct_option = (
            cleaned_data.get(
                "correct_option"
            )
        )

        option_c = (
            cleaned_data.get(
                "option_c"
            )
        )

        option_d = (
            cleaned_data.get(
                "option_d"
            )
        )

        if (
            correct_option == "C"
            and not option_c
        ):

            self.add_error(
                "correct_option",
                (
                    "Option C is empty."
                ),
            )

        if (
            correct_option == "D"
            and not option_d
        ):

            self.add_error(
                "correct_option",
                (
                    "Option D is empty."
                ),
            )

        return cleaned_data