from functools import wraps

from django.contrib.auth.decorators import login_required
from django.shortcuts import render


def role_required(*allowed_roles):
    """
    Restrict a view to specific Lakdiva SecurePOS roles.

    Example:

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

            # User must have a role.
            if not getattr(user, "role", None):

                return render(
                    request,
                    "errors/403.html",
                    status=403,
                )

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