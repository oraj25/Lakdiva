from django.contrib import admin
from django.contrib.auth.admin import (
    UserAdmin as BaseUserAdmin,
)

from .forms import (
    UserChangeForm,
    UserCreationForm,
)

from .models import (
    LoginAttempt,
    Role,
    User,
)


# =========================================================
# ROLE ADMIN
# =========================================================

@admin.register(Role)
class RoleAdmin(admin.ModelAdmin):

    list_display = [
        "role_id",
        "role_name",
    ]

    search_fields = [
        "role_name",
    ]


# =========================================================
# USER ADMIN
# =========================================================

@admin.register(User)
class UserAdmin(BaseUserAdmin):

    form = UserChangeForm

    add_form = UserCreationForm

    model = User

    list_display = [
        "staff_no",
        "full_name",
        "email",
        "role",
        "status",
        "is_staff",
    ]

    list_filter = [
        "role",
        "status",
        "is_staff",
        "is_superuser",
    ]

    search_fields = [
        "staff_no",
        "full_name",
        "email",
    ]

    ordering = [
        "staff_no",
    ]

    readonly_fields = [
        "last_login",
        "created_at",
        "updated_at",
    ]

    fieldsets = [
        (
            None,
            {
                "fields": [
                    "email",
                    "password",
                ]
            },
        ),
        (
            "Employee Information",
            {
                "fields": [
                    "staff_no",
                    "full_name",
                ]
            },
        ),
        (
            "Lakdiva Access",
            {
                "fields": [
                    "role",
                    "status",
                ]
            },
        ),
        (
            "Django Permissions",
            {
                "fields": [
                    "is_staff",
                    "is_superuser",
                    "groups",
                    "user_permissions",
                ]
            },
        ),
        (
            "Important Dates",
            {
                "fields": [
                    "last_login",
                    "created_at",
                    "updated_at",
                ]
            },
        ),
    ]

    add_fieldsets = [
        (
            None,
            {
                "classes": [
                    "wide"
                ],
                "fields": [
                    "email",
                    "staff_no",
                    "full_name",
                    "role",
                    "status",
                    "password1",
                    "password2",
                    "is_staff",
                    "is_superuser",
                ],
            },
        ),
    ]

    filter_horizontal = [
        "groups",
        "user_permissions",
    ]

# =========================================================
# LOGIN ATTEMPT ADMIN
# =========================================================

@admin.register(LoginAttempt)
class LoginAttemptAdmin(admin.ModelAdmin):

    list_display = [
        "attempt_id",
        "login_identifier",
        "user",
        "success",
        "ip_address",
        "attempted_at",
    ]

    list_filter = [
        "success",
        "attempted_at",
    ]

    search_fields = [
        "login_identifier",
        "user__email",
        "user__staff_no",
        "user__full_name",
    ]

    ordering = [
        "-attempted_at",
    ]

    readonly_fields = [
        "login_identifier",
        "user",
        "success",
        "ip_address",
        "attempted_at",
    ]

    def has_add_permission(
        self,
        request,
    ):
        return False

    def has_change_permission(
        self,
        request,
        obj=None,
    ):
        return False

    def has_delete_permission(
        self,
        request,
        obj=None,
    ):
        return False