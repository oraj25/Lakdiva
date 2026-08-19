from functools import wraps

from django.contrib.auth.decorators import login_required
from django.core.exceptions import PermissionDenied
from django.shortcuts import render


# =========================================================
# ROLE-BASED ACCESS CONTROL
# =========================================================

def role_required(*allowed_roles):
    """
    Restrict a view to specific Lakdiva SecurePOS roles.

    Examples:

    @role_required("ADMIN")

    @role_required("EMPLOYEE")
    """

    def decorator(view_function):

        @wraps(view_function)
        @login_required
        def wrapper(
            request,
            *args,
            **kwargs,
        ):

            user = request.user

            # User must have an assigned application role.
            if not getattr(
                user,
                "role",
                None,
            ):

                return render(
                    request,
                    "errors/403.html",
                    status=403,
                )

            # User's role must be one of the permitted roles.
            if (
                user.role.role_name
                not in allowed_roles
            ):

                return render(
                    request,
                    "errors/403.html",
                    status=403,
                )

            return view_function(
                request,
                *args,
                **kwargs,
            )

        return wrapper

    return decorator


# =========================================================
# ADMINISTRATOR ACCESS CONTROL
# =========================================================

def admin_required(view_func):

    @wraps(view_func)
    @login_required
    def wrapper(
        request,
        *args,
        **kwargs,
    ):

        user = request.user

        if not user.is_authenticated:
            raise PermissionDenied

        if not getattr(user, "role", None):
            raise PermissionDenied

        if user.role.role_name != user.role.ADMIN:
            raise PermissionDenied

        return view_func(
            request,
            *args,
            **kwargs,
        )

    return wrapper