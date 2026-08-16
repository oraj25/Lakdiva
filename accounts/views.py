from django.contrib import messages

from django.contrib.auth import (
    authenticate,
    get_user_model,
    login as auth_login,
    logout as auth_logout,
)

from django.contrib.auth.decorators import login_required

from django.shortcuts import (
    redirect,
    render,
)

from django.views.decorators.http import require_POST

from .decorators import role_required
from .forms import LoginForm
from .models import LoginAttempt, Role


# =========================================================
# HELPER FUNCTIONS
# =========================================================

def get_client_ip(request):
    """
    Return the direct client IP address.

    For local development this normally returns:
    127.0.0.1
    """

    return request.META.get(
        "REMOTE_ADDR"
    )


def find_user_by_identifier(identifier):
    """
    Find a user for login-attempt logging.

    This function does NOT authenticate the user.
    """

    User = get_user_model()

    identifier = identifier.strip()

    try:
        return User.objects.get(
            email__iexact=identifier
        )

    except User.DoesNotExist:

        try:
            return User.objects.get(
                staff_no__iexact=identifier
            )

        except User.DoesNotExist:
            return None


def redirect_user_by_role(user):
    """
    Send an authenticated user to the correct dashboard.
    """

    if not getattr(user, "role", None):

        return redirect("login")

    role = user.role.role_name

    if role == Role.ADMIN:

        return redirect(
            "administrator_dashboard"
        )

    if role == Role.EMPLOYEE:

        return redirect(
            "employee_dashboard"
        )

    return redirect("login")


# =========================================================
# HOME
# =========================================================

def home_redirect(request):

    if not request.user.is_authenticated:

        return redirect("login")

    return redirect_user_by_role(
        request.user
    )


# =========================================================
# LOGIN
# =========================================================

def login_view(request):

    # Already logged-in users should not see
    # the login page again.
    if request.user.is_authenticated:

        return redirect_user_by_role(
            request.user
        )

    form = LoginForm(
        request.POST or None
    )

    if request.method == "POST":

        if form.is_valid():

            identifier = (
                form.cleaned_data[
                    "identifier"
                ].strip()
            )

            password = (
                form.cleaned_data[
                    "password"
                ]
            )

            # ---------------------------------------------
            # Authenticate
            # ---------------------------------------------

            user = authenticate(
                request,
                username=identifier,
                password=password,
            )

            # ---------------------------------------------
            # Record login attempt
            # ---------------------------------------------

            matched_user = (
                user
                or find_user_by_identifier(
                    identifier
                )
            )

            LoginAttempt.objects.create(
                login_identifier=identifier,
                user=matched_user,
                success=user is not None,
                ip_address=get_client_ip(
                    request
                ),
            )

            # ---------------------------------------------
            # Successful login
            # ---------------------------------------------

            if user is not None:

                auth_login(
                    request,
                    user,
                )

                messages.success(
                    request,
                    "Login successful."
                )

                return redirect_user_by_role(
                    user
                )

            # ---------------------------------------------
            # Failed login
            # ---------------------------------------------

            messages.error(
                request,
                (
                    "Invalid login credentials "
                    "or the account is unavailable."
                ),
            )

    return render(
        request,
        "accounts/login.html",
        {
            "form": form,
        },
    )


# =========================================================
# LOGOUT
# =========================================================

@login_required
@require_POST
def logout_view(request):

    auth_logout(request)

    messages.success(
        request,
        "You have been logged out."
    )

    return redirect("login")


# =========================================================
# EMPLOYEE DASHBOARD
# =========================================================

@role_required(Role.EMPLOYEE)
def employee_dashboard(request):

    return render(
        request,
        "employee/dashboard.html",
    )


# =========================================================
# ADMINISTRATOR DASHBOARD
# =========================================================

@role_required(Role.ADMIN)
def administrator_dashboard(request):

    return render(
        request,
        "administrator/dashboard.html",
    )