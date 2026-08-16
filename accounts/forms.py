from django import forms
from django.contrib.auth.forms import (
    ReadOnlyPasswordHashField,
)

from .models import User


# =========================================================
# USER CREATION FORM
# =========================================================

class UserCreationForm(forms.ModelForm):

    password1 = forms.CharField(
        label="Password",
        widget=forms.PasswordInput,
    )

    password2 = forms.CharField(
        label="Confirm Password",
        widget=forms.PasswordInput,
    )

    class Meta:
        model = User

        fields = [
            "email",
            "staff_no",
            "full_name",
            "role",
            "status",
        ]

    def clean_password2(self):

        password1 = self.cleaned_data.get(
            "password1"
        )

        password2 = self.cleaned_data.get(
            "password2"
        )

        if (
            password1
            and password2
            and password1 != password2
        ):
            raise forms.ValidationError(
                "Passwords do not match."
            )

        return password2

    def save(self, commit=True):

        user = super().save(
            commit=False
        )

        user.set_password(
            self.cleaned_data["password1"]
        )

        if commit:
            user.save()

        return user


# =========================================================
# USER CHANGE FORM
# =========================================================

class UserChangeForm(forms.ModelForm):

    password = ReadOnlyPasswordHashField(
        label="Password"
    )

    class Meta:
        model = User

        fields = [
            "email",
            "staff_no",
            "full_name",
            "password",
            "role",
            "status",
            "is_staff",
            "is_superuser",
        ]

    def clean_password(self):

        return self.initial.get(
            "password"
        )


# =========================================================
# LOGIN FORM
# =========================================================

class LoginForm(forms.Form):

    identifier = forms.CharField(
        label="Email or Staff Number",
        max_length=254,
        widget=forms.TextInput(
            attrs={
                "class": "form-control",
                "placeholder": "Email or Staff Number",
                "autocomplete": "username",
            }
        ),
    )

    password = forms.CharField(
        label="Password",
        widget=forms.PasswordInput(
            attrs={
                "class": "form-control",
                "placeholder": "Password",
                "autocomplete": "current-password",
            }
        ),
    )