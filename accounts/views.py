from decimal import Decimal

from django.contrib import messages

from django.contrib.auth import (
    authenticate,
    get_user_model,
    login as auth_login,
    logout as auth_logout,
)

from django.contrib.auth.decorators import (
    login_required,
)

from django.contrib.auth.forms import (
    SetPasswordForm,
)

from django.db.models import (
    Avg,
    OuterRef,
    Subquery,
)

from django.shortcuts import (
    get_object_or_404,
    redirect,
    render,
)

from django.utils import timezone

from django.views.decorators.http import (
    require_POST,
)

from .decorators import (
    admin_required,
    role_required,
)

from .forms import (
    AdminUserCreateForm,
    AdminUserUpdateForm,
    LoginForm,
)

from .models import (
    LoginAttempt,
    Role,
)

from policies.models import (
    EMPLOYEE_POLICY_TYPES,
    Policy,
    PolicyAcknowledgement,
)

from training.models import (
    EmployeeTraining,
)

from training_needs.models import (
    TrainingNeed,
)

from pos_security.models import (
    DailySecurityCheck,
    POSShift,
)

from incidents.models import (
    Incident,
    IncidentRiskAssessment,
)

from compliance.models import (
    ComplianceSummary,
)

from compliance.services import (
    recalculate_all_employee_compliance,
)

from notifications.models import (
    Notification,
)

from notifications.utils import (
    sync_employee_reminders,
)

from auditlog.utils import (
    log_action,
)


# =========================================================
# CURRENT USER MODEL
# =========================================================

User = get_user_model()

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

    if not getattr(
        user,
        "role",
        None,
    ):

        return redirect(
            "login"
        )

    role = (
        user.role.role_name
    )

    if role == Role.ADMIN:

        return redirect(
            "administrator_dashboard"
        )

    if role == Role.EMPLOYEE:

        return redirect(
            "employee_dashboard"
        )

    return redirect(
        "login"
    )


# =========================================================
# HOME
# =========================================================

def home_redirect(request):

    if not request.user.is_authenticated:

        return redirect(
            "login"
        )

    return redirect_user_by_role(
        request.user
    )


# =========================================================
# LOGIN
# =========================================================

def login_view(request):

    # -----------------------------------------------------
    # ALREADY LOGGED IN
    # -----------------------------------------------------

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

            # -------------------------------------------------
            # AUTHENTICATE
            # -------------------------------------------------

            user = authenticate(
                request,
                username=identifier,
                password=password,
            )

            # -------------------------------------------------
            # FIND USER FOR LOGIN-ATTEMPT RECORD
            # -------------------------------------------------

            matched_user = (
                user
                or find_user_by_identifier(
                    identifier
                )
            )

            # -------------------------------------------------
            # RECORD LOGIN ATTEMPT
            # -------------------------------------------------

            LoginAttempt.objects.create(
                login_identifier=identifier,
                user=matched_user,
                success=user is not None,
                ip_address=get_client_ip(
                    request
                ),
            )

            # -------------------------------------------------
            # SUCCESSFUL LOGIN
            # -------------------------------------------------

            if user is not None:

                auth_login(
                    request,
                    user,
                )

                # ---------------------------------------------
                # AUDIT SUCCESSFUL LOGIN
                # ---------------------------------------------

                log_action(
                    request=request,
                    action="LOGIN_SUCCESS",
                    entity_type="User",
                    entity_id=user.user_id,
                    user=user,
                    details=(
                        f"Successful login for "
                        f"{user.staff_no}."
                    ),
                )

                messages.success(
                    request,
                    "Login successful."
                )

                return redirect_user_by_role(
                    user
                )

            # -------------------------------------------------
            # FAILED LOGIN AUDIT
            # -------------------------------------------------

            log_action(
                request=request,
                action="LOGIN_FAILED",
                entity_type="Authentication",
                entity_id=None,
                details=(
                    f"Failed login attempt for "
                    f"identifier "
                    f"'{identifier}'."
                ),
            )

            # -------------------------------------------------
            # FAILED LOGIN MESSAGE
            # -------------------------------------------------

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
def logout_view(
    request,
):

    # -----------------------------------------------------
    # STORE USER BEFORE LOGOUT
    # -----------------------------------------------------

    user = request.user

    # -----------------------------------------------------
    # AUDIT LOG
    # -----------------------------------------------------

    log_action(
        request=request,
        action="LOGOUT",
        entity_type="User",
        entity_id=user.user_id,
        user=user,
        details=(
            f"User "
            f"{user.staff_no} "
            f"logged out."
        ),
    )

    # -----------------------------------------------------
    # LOGOUT
    # -----------------------------------------------------

    auth_logout(
        request
    )

    messages.success(
        request,
        "You have been logged out."
    )

    return redirect(
        "login"
    )
# =========================================================
# EMPLOYEE DASHBOARD
# =========================================================

@role_required(Role.EMPLOYEE)
def employee_dashboard(request):

    # -----------------------------------------------------
    # DAILY NOTIFICATION REMINDERS
    # -----------------------------------------------------

    sync_employee_reminders(
        request.user
    )

    # -----------------------------------------------------
    # OPEN POS SHIFT
    # -----------------------------------------------------

    open_shift = (
        POSShift.objects
        .filter(
            user=request.user,
            status=(
                POSShift.Status.OPEN
            ),
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
        Policy.objects
        .filter(
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
        PolicyAcknowledgement.objects
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

            "open_shift": (
                open_shift
            ),
        },
    )


# =========================================================
# ADMINISTRATOR DASHBOARD
# =========================================================

@role_required(Role.ADMIN)
def administrator_dashboard(
    request,
):

    User = get_user_model()

    # =====================================================
    # REFRESH COMPLIANCE SNAPSHOTS
    # =====================================================

    recalculate_all_employee_compliance()


    # =====================================================
    # ACTIVE EMPLOYEES
    # =====================================================

    active_employees = (
        User.objects
        .filter(
            role__role_name=(
                Role.EMPLOYEE
            ),
            status=(
                User.Status.ACTIVE
            ),
        )
    )

    active_employee_count = (
        active_employees.count()
    )


    # =====================================================
    # COMPLIANCE SUMMARY
    # =====================================================

    compliance_records = (
        ComplianceSummary.objects
        .filter(
            user__role__role_name=(
                Role.EMPLOYEE
            ),
            user__status=(
                User.Status.ACTIVE
            ),
        )
    )


    overall_policy_compliance = (
        compliance_records
        .aggregate(
            value=Avg(
                "policy_compliance"
            )
        )["value"]
        or Decimal("0")
    )


    overall_pos_compliance = (
        compliance_records
        .aggregate(
            value=Avg(
                "pos_check_compliance"
            )
        )["value"]
        or Decimal("0")
    )


    average_employee_score = (
        compliance_records
        .aggregate(
            value=Avg(
                "employee_score"
            )
        )["value"]
        or Decimal("0")
    )


    # =====================================================
    # TRAINING COMPLETION
    # =====================================================

    training_assignments = (
        EmployeeTraining.objects
        .filter(
            user__role__role_name=(
                Role.EMPLOYEE
            )
        )
    )


    total_training_assignments = (
        training_assignments.count()
    )


    completed_training_assignments = (
        training_assignments
        .filter(
            status=(
                EmployeeTraining
                .Status
                .COMPLETED
            )
        )
        .count()
    )


    if total_training_assignments:

        training_completion = (
            Decimal(
                completed_training_assignments
            )
            /
            Decimal(
                total_training_assignments
            )
            *
            Decimal("100")
        )

    else:

        training_completion = (
            Decimal("100")
        )


    # =====================================================
    # INCIDENTS + LATEST RISK
    # =====================================================

    latest_risk_query = (
        IncidentRiskAssessment.objects
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


    incidents_with_risk = (
        Incident.objects
        .annotate(
            current_risk=(
                Subquery(
                    latest_risk_query
                )
            )
        )
    )


    open_incident_count = (
        incidents_with_risk
        .exclude(
            status=(
                Incident.Status.RESOLVED
            )
        )
        .count()
    )


    high_risk_incident_count = (
        incidents_with_risk
        .exclude(
            status=(
                Incident.Status.RESOLVED
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


    recent_incidents = (
        incidents_with_risk
        .select_related(
            "reported_by",
            "category",
            "pos",
        )
        .order_by(
            "-created_at"
        )[:5]
    )


    # =====================================================
    # TRAINING NEEDS
    # =====================================================

    open_training_need_count = (
        TrainingNeed.objects
        .filter(
            status=(
                TrainingNeed
                .Status
                .OPEN
            )
        )
        .count()
    )


    high_training_need_count = (
        TrainingNeed.objects
        .filter(
            status=(
                TrainingNeed
                .Status
                .OPEN
            ),
            priority=(
                TrainingNeed
                .Priority
                .HIGH
            ),
        )
        .count()
    )


    recent_training_needs = (
        TrainingNeed.objects
        .filter(
            status=(
                TrainingNeed
                .Status
                .OPEN
            )
        )
        .select_related(
            "user",
            "training",
        )
        .order_by(
            "-identified_at"
        )[:5]
    )


    # =====================================================
    # TODAY'S POS SECURITY
    # =====================================================

    today = timezone.localdate()


    security_checks_today = (
        DailySecurityCheck.objects
        .filter(
            checked_at__date=today
        )
        .count()
    )


    suspicious_checks_today = (
        DailySecurityCheck.objects
        .filter(
            checked_at__date=today,
            result=(
                DailySecurityCheck
                .Result
                .SUSPICIOUS
            ),
        )
        .count()
    )


    # =====================================================
    # NOTIFICATIONS
    # =====================================================

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

    # =====================================================
    # RENDER ADMINISTRATOR DASHBOARD
    # =====================================================

    return render(
        request,
        "administrator/dashboard.html",
        {
            "active_employee_count": (
                active_employee_count
            ),

            "overall_policy_compliance": (
                overall_policy_compliance
            ),

            "training_completion": (
                training_completion
            ),

            "overall_pos_compliance": (
                overall_pos_compliance
            ),

            "average_employee_score": (
                average_employee_score
            ),

            "open_incident_count": (
                open_incident_count
            ),

            "high_risk_incident_count": (
                high_risk_incident_count
            ),

            "open_training_need_count": (
                open_training_need_count
            ),

            "high_training_need_count": (
                high_training_need_count
            ),

            "security_checks_today": (
                security_checks_today
            ),

            "suspicious_checks_today": (
                suspicious_checks_today
            ),

            "recent_incidents": (
                recent_incidents
            ),

            "recent_training_needs": (
                recent_training_needs
            ),

            "unread_notification_count": (
                unread_notification_count
            ),

            "recent_notifications": (
                recent_notifications
            ),
        },
    )


# =========================================================
# ADMIN USER MANAGEMENT - USER LIST
# =========================================================

@admin_required
def admin_user_list(
    request,
):

    users = (
        User.objects
        .select_related(
            "role"
        )
        .all()
        .order_by(
            "staff_no"
        )
    )

    return render(
        request,
        "accounts/admin/user_list.html",
        {
            "users": users,
        },
    )


# =========================================================
# ADMIN USER MANAGEMENT - CREATE USER
# =========================================================

@admin_required
def admin_user_create(
    request,
):

    if request.method == "POST":

        form = AdminUserCreateForm(
            request.POST
        )

        if form.is_valid():

            user = form.save()

            messages.success(
                request,
                "User created successfully.",
            )

            return redirect(
                "admin_user_list"
            )

    else:

        form = AdminUserCreateForm()

    return render(
        request,
        "accounts/admin/user_form.html",
        {
            "form": form,
            "page_title": "Add User",
        },
    )


# =========================================================
# ADMIN USER MANAGEMENT - EDIT USER
# =========================================================

@admin_required
def admin_user_edit(
    request,
    user_id,
):

    user = get_object_or_404(
        User,
        pk=user_id,
    )

    if request.method == "POST":

        form = AdminUserUpdateForm(
            request.POST,
            instance=user,
        )

        if form.is_valid():

            if (
                user == request.user
                and "is_staff" in form.fields
                and not form.cleaned_data.get(
                    "is_staff"
                )
            ):

                form.add_error(
                    "is_staff",
                    (
                        "You cannot remove your own "
                        "administrator access."
                    ),
                )

            else:

                form.save()

                messages.success(
                    request,
                    "User updated successfully.",
                )

                return redirect(
                    "admin_user_list"
                )

    else:

        form = AdminUserUpdateForm(
            instance=user
        )

    return render(
        request,
        "accounts/admin/user_form.html",
        {
            "form": form,
            "page_title": "Edit User",
            "target_user": user,
        },
    )


# =========================================================
# ADMIN USER MANAGEMENT - USER DETAILS
# =========================================================

@admin_required
def admin_user_detail(
    request,
    user_id,
):

    user = get_object_or_404(
        User,
        pk=user_id,
    )

    return render(
        request,
        "accounts/admin/user_detail.html",
        {
            "target_user": user,
        },
    )


# =========================================================
# ADMIN USER MANAGEMENT - ENABLE / DISABLE USER
# =========================================================

@admin_required
@require_POST
def admin_toggle_user(
    request,
    user_id,
):

    user = get_object_or_404(
        User,
        pk=user_id,
    )

    # -----------------------------------------------------
    # PREVENT SELF-DISABLING
    # -----------------------------------------------------

    if user == request.user:

        messages.error(
            request,
            "You cannot disable your own account.",
        )

        return redirect(
            "admin_user_list"
        )


    # -----------------------------------------------------
    # ACTIVE -> DISABLED
    # -----------------------------------------------------

    if (
        user.status
        == User.Status.ACTIVE
    ):

        user.status = (
            User.Status.DISABLED
        )

        message = (
            "User account disabled successfully."
        )


    # -----------------------------------------------------
    # DISABLED -> ACTIVE
    # -----------------------------------------------------

    else:

        user.status = (
            User.Status.ACTIVE
        )

        message = (
            "User account enabled successfully."
        )


    # -----------------------------------------------------
    # SAVE STATUS
    # -----------------------------------------------------

    user.save(
        update_fields=[
            "status",
            "updated_at",
        ]
    )


    # -----------------------------------------------------
    # AUDIT LOG
    # -----------------------------------------------------

    log_action(
        request=request,

        action=(
            "USER_DISABLED"
            if (
                user.status
                == User.Status.DISABLED
            )
            else
            "USER_ENABLED"
        ),

        entity_type="User",

        entity_id=user.pk,

        details=(
            f"Administrator "
            f"{request.user.staff_no} "
            f"{'disabled' if user.status == User.Status.DISABLED else 'enabled'} "
            f"user {user.staff_no}."
        ),
    )


    # -----------------------------------------------------
    # SUCCESS MESSAGE
    # -----------------------------------------------------

    messages.success(
        request,
        message,
    )


    return redirect(
        "admin_user_list"
    )

# =========================================================
# ADMIN USER MANAGEMENT - RESET PASSWORD
# =========================================================

@admin_required
def admin_reset_password(
    request,
    user_id,
):

    user = get_object_or_404(
        User,
        pk=user_id,
    )

    if request.method == "POST":

        form = SetPasswordForm(
            user,
            request.POST,
        )

        if form.is_valid():

            form.save()

            messages.success(
                request,
                (
                    "User password has "
                    "been reset."
                ),
            )

            return redirect(
                "admin_user_detail",
                user_id=user.pk,
            )

    else:

        form = SetPasswordForm(
            user
        )

    return render(
        request,
        "accounts/admin/reset_password.html",
        {
            "form": form,
            "target_user": user,
        },
    )