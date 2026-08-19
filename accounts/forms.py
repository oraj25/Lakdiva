from django import forms

from django.contrib.auth import (
    get_user_model,
    password_validation,
)

from django.contrib.auth.forms import (
    ReadOnlyPasswordHashField,
)

from .models import (
    Role,
    User,
)


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

    def save(
        self,
        commit=True,
    ):

        user = super().save(
            commit=False
        )

        user.set_password(
            self.cleaned_data["password1"]
        )

        user.is_staff = (
            user.role.role_name
            == Role.ADMIN
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


# =========================================================
# CURRENT USER MODEL
# =========================================================

User = get_user_model()


# =========================================================
# ADMIN - CREATE USER FORM
# =========================================================

class AdminUserCreateForm(forms.ModelForm):

    password1 = forms.CharField(
        label="Password",
        widget=forms.PasswordInput(
            attrs={
                "class": "form-control",
                "autocomplete": "new-password",
            }
        ),
        strip=False,
    )

    password2 = forms.CharField(
        label="Confirm Password",
        widget=forms.PasswordInput(
            attrs={
                "class": "form-control",
                "autocomplete": "new-password",
            }
        ),
        strip=False,
    )

    class Meta:

        model = User

        fields = (
            "staff_no",
            "full_name",
            "email",
            "role",
            "status",
        )

        widgets = {
            "staff_no": forms.TextInput(
                attrs={
                    "class": "form-control",
                }
            ),
            "full_name": forms.TextInput(
                attrs={
                    "class": "form-control",
                }
            ),
            "email": forms.EmailInput(
                attrs={
                    "class": "form-control",
                }
            ),
            "role": forms.Select(
                attrs={
                    "class": "form-control",
                }
            ),
            "status": forms.Select(
                attrs={
                    "class": "form-control",
                }
            ),
        }

        labels = {
            "staff_no": "Staff Number",
            "full_name": "Full Name",
            "email": "Email",
            "role": "Role",
            "status": "Account Status",
        }

    def __init__(
        self,
        *args,
        **kwargs,
    ):

        super().__init__(
            *args,
            **kwargs,
        )

        # Only valid application roles can be assigned.
        self.fields[
            "role"
        ].queryset = (
            Role.objects.filter(
                role_name__in=(
                    Role.ADMIN,
                    Role.EMPLOYEE,
                )
            )
        )

        # Default values for a new user.
        if not self.is_bound:

            employee_role = (
                Role.objects.filter(
                    role_name=Role.EMPLOYEE
                ).first()
            )

            if employee_role:

                self.fields[
                    "role"
                ].initial = (
                    employee_role
                )

            self.fields[
                "status"
            ].initial = (
                User.Status.ACTIVE
            )

    def clean_password1(self):

        password = self.cleaned_data.get(
            "password1"
        )

        if password:

            password_validation.validate_password(
                password
            )

        return password

    def clean(self):

        cleaned_data = super().clean()

        password1 = cleaned_data.get(
            "password1"
        )

        password2 = cleaned_data.get(
            "password2"
        )

        if (
            password1
            and password2
            and password1 != password2
        ):

            self.add_error(
                "password2",
                "Passwords do not match.",
            )

        return cleaned_data

    def save(
        self,
        commit=True,
    ):

        user = super().save(
            commit=False
        )

        user.set_password(
            self.cleaned_data[
                "password1"
            ]
        )

        # Administrator role receives Django staff access.
        user.is_staff = (
            user.role.role_name
            == Role.ADMIN
        )

        if commit:

            user.save()

        return user


# =========================================================
# ADMIN - UPDATE USER FORM
# =========================================================

class AdminUserUpdateForm(forms.ModelForm):

    class Meta:

        model = User

        fields = (
            "staff_no",
            "full_name",
            "email",
            "role",
            "status",
        )

        widgets = {

            "staff_no": forms.TextInput(
                attrs={
                    "class": "form-control",
                }
            ),

            "full_name": forms.TextInput(
                attrs={
                    "class": "form-control",
                }
            ),

            "email": forms.EmailInput(
                attrs={
                    "class": "form-control",
                }
            ),

            "role": forms.Select(
                attrs={
                    "class": "form-control",
                }
            ),

            "status": forms.Select(
                attrs={
                    "class": "form-control",
                }
            ),
        }

        labels = {

            "staff_no": "Staff Number",

            "full_name": "Full Name",

            "email": "Email",

            "role": "Role",

            "status": "Account Status",
        }

    def __init__(
        self,
        *args,
        **kwargs,
    ):

        super().__init__(
            *args,
            **kwargs,
        )

        self.fields[
            "role"
        ].queryset = (
            Role.objects.filter(
                role_name__in=(
                    Role.ADMIN,
                    Role.EMPLOYEE,
                )
            )
        )

    def save(
        self,
        commit=True,
    ):

        user = super().save(
            commit=False
        )

        # Keep Django's staff permission
        # synchronized with the application role.
        user.is_staff = (
            user.role.role_name
            == Role.ADMIN
        )

        if commit:

            user.save()

        return user