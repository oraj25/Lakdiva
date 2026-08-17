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

from policies.models import (
    EMPLOYEE_POLICY_TYPES,
    Policy,
    PolicyAcknowledgement,
)

from django.db.models import (
    OuterRef,
    Subquery,
)

from training.models import (
    EmployeeTraining,
)

from pos_security.models import (
    POSShift,
)

from incidents.models import (
    Incident,
    IncidentRiskAssessment,
)

from notifications.models import (
    Notification,
)


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
    open_shift = (
    POSShift.objects
    .filter(
        user=request.user,
        status=POSShift.Status.OPEN,
    )
    .select_related(
        "pos"
    )
    .first()
)

    

    # -----------------------------------------------------
    # POLICY COUNT
    # -----------------------------------------------------

    published_policies = (
        Policy.objects.filter(
            status=(
                Policy.Status.PUBLISHED
            ),
            policy_type__in=(
                EMPLOYEE_POLICY_TYPES
            ),
        )
    )

    total_policies = (
        published_policies.count()
    )

    acknowledged_policies = (
        PolicyAcknowledgement
        .objects
        .filter(
            user=request.user,
            policy__in=(
                published_policies
            ),
        )
        .count()
    )

    pending_policy_count = max(
        total_policies
        - acknowledged_policies,
        0,
    )


    # -----------------------------------------------------
    # TRAINING COUNT
    # -----------------------------------------------------

    pending_training_count = (
        EmployeeTraining.objects
        .filter(
            user=request.user
        )
        .exclude(
            status=(
                EmployeeTraining
                .Status
                .COMPLETED
            )
        )
        .count()
    )


    # -----------------------------------------------------
    # DASHBOARD
    # -----------------------------------------------------

    return render(
        request,
        "employee/dashboard.html",
        {
            "pending_policy_count": (
                pending_policy_count
            ),

            "pending_training_count": (
                pending_training_count
            ),

            "open_shift": open_shift,
        },
    )
# =========================================================
# ADMINISTRATOR DASHBOARD
# =========================================================

@role_required(Role.ADMIN)
def administrator_dashboard(request):

    pending_incident_count = (
        Incident.objects
        .exclude(
            status=(
                Incident.Status.RESOLVED
            )
        )
        .count()
    )

    # ---------------------------------------------------------
    # LATEST RISK LEVEL FOR EACH INCIDENT
    # ---------------------------------------------------------

    latest_risk_query = (
        IncidentRiskAssessment
        .objects
        .filter(
            incident_id=OuterRef(
                "pk"
            )
        )
        .order_by(
            "-assessed_at"
        )
        .values(
            "risk_level"
        )[:1]
    )


    # ---------------------------------------------------------
    # HIGH-RISK OPEN INCIDENT COUNT
    # ---------------------------------------------------------

    high_risk_incident_count = (
        Incident.objects
        .exclude(
            status=(
                Incident.Status.RESOLVED
            )
        )
        .annotate(
            current_risk=(
                Subquery(
                    latest_risk_query
                )
            )
        )
        .filter(
            current_risk=(
                IncidentRiskAssessment
                .RiskLevel
                .HIGH
            )
        )
        .count()
    )

    

    unread_notification_count = (
        Notification.objects
        .filter(
            user=request.user,
            is_read=False,
        )
        .count()
    )

    recent_notifications = (
        Notification.objects
        .filter(
            user=request.user,
            is_read=False,
        )
        .order_by(
            "-created_at"
        )[:5]
    )

    return render(
        request,
        (
            "administrator/"
            "dashboard.html"
        ),
        {
            "pending_incident_count": (
                pending_incident_count
            ),

            "unread_notification_count": (
                unread_notification_count
            ),

            "recent_notifications": (
                recent_notifications
            ),
            "high_risk_incident_count": (
                high_risk_incident_count
            ),
        },
    )