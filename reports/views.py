import csv

from decimal import Decimal

from django.db.models import (
    Avg,
    OuterRef,
    Subquery,
)

from django.http import (
    HttpResponse,
    HttpResponseBadRequest,
)

from django.shortcuts import render

from django.utils import timezone

from accounts.decorators import (
    role_required,
)

from accounts.models import (
    Role,
    User,
)

from auditlog.utils import (
    log_action,
)

from compliance.models import (
    ComplianceSummary,
)

from compliance.services import (
    recalculate_all_employee_compliance,
)

from incidents.models import (
    Incident,
    IncidentRiskAssessment,
)

from pos_security.models import (
    DailySecurityCheck,
    POSShift,
)

from training.models import (
    EmployeeTraining,
)

from training_needs.models import (
    TrainingNeed,
)

from .forms import (
    SecurityReportFilterForm,
)


# =========================================================
# CSV SECURITY HELPER
# =========================================================

def safe_csv_value(value):

    if value is None:
        return ""

    if isinstance(
        value,
        (
            int,
            float,
            Decimal,
        ),
    ):
        return value

    text = str(value)

    # Protect CSV output from spreadsheet
    # formula injection.

    if text.startswith(
        (
            "=",
            "+",
            "-",
            "@",
        )
    ):

        return "'" + text

    return text


# =========================================================
# DATE FILTER HELPER
# =========================================================

def get_report_dates(request):

    form = SecurityReportFilterForm(
        request.GET or None
    )

    if not form.is_valid():

        return (
            form,
            None,
            None,
        )

    return (
        form,
        form.cleaned_data.get(
            "date_from"
        ),
        form.cleaned_data.get(
            "date_to"
        ),
    )


# =========================================================
# REPORT CENTER
# =========================================================

@role_required(Role.ADMIN)
def report_center(request):

    form, date_from, date_to = (
        get_report_dates(
            request
        )
    )

    if not form.is_valid():

        date_from = None
        date_to = None


    active_employee_count = (
        User.objects.filter(
            role__role_name=(
                Role.EMPLOYEE
            ),
            status=User.Status.ACTIVE,
        ).count()
    )


    open_incident_count = (
        Incident.objects.exclude(
            status=(
                Incident.Status.RESOLVED
            )
        ).count()
    )


    open_training_need_count = (
        TrainingNeed.objects.filter(
            status=(
                TrainingNeed
                .Status
                .OPEN
            )
        ).count()
    )


    average_employee_score = (
        ComplianceSummary.objects
        .filter(
            user__role__role_name=(
                Role.EMPLOYEE
            ),
            user__status=(
                User.Status.ACTIVE
            ),
        )
        .aggregate(
            value=Avg(
                "employee_score"
            )
        )["value"]
        or Decimal("0")
    )


    return render(
        request,
        (
            "administrator/"
            "reports/index.html"
        ),
        {
            "form": form,

            "active_employee_count": (
                active_employee_count
            ),

            "open_incident_count": (
                open_incident_count
            ),

            "open_training_need_count": (
                open_training_need_count
            ),

            "average_employee_score": (
                average_employee_score
            ),
        },
    )


# =========================================================
# COMPLIANCE CSV REPORT
# =========================================================

@role_required(Role.ADMIN)
def compliance_csv(request):

    recalculate_all_employee_compliance()

    summaries = (
        ComplianceSummary.objects
        .filter(
            user__role__role_name=(
                Role.EMPLOYEE
            )
        )
        .select_related(
            "user"
        )
        .order_by(
            "user__staff_no"
        )
    )


    response = HttpResponse(
        content_type=(
            "text/csv; charset=utf-8"
        )
    )

    filename = (
        "lakdiva_compliance_"
        f"{timezone.localdate()}.csv"
    )

    response[
        "Content-Disposition"
    ] = (
        f'attachment; filename="{filename}"'
    )


    writer = csv.writer(
        response
    )

    writer.writerow(
        [
            "Staff No",
            "Employee",
            "Policy Compliance %",
            "Training Compliance %",
            "POS Check Compliance %",
            "Employee Score %",
            "Last Calculated",
        ]
    )


    for summary in summaries:

        writer.writerow(
            [
                safe_csv_value(
                    summary.user.staff_no
                ),

                safe_csv_value(
                    summary.user.full_name
                ),

                summary.policy_compliance,

                summary.training_compliance,

                summary.pos_check_compliance,

                summary.employee_score,

                summary.last_calculated_at,
            ]
        )


    log_action(
        request=request,
        action="REPORT_GENERATED",
        entity_type="ComplianceReport",
        entity_id=None,
        details=(
            "Administrator generated "
            "the employee compliance report."
        ),
    )

    return response


# =========================================================
# TRAINING CSV REPORT
# =========================================================

@role_required(Role.ADMIN)
def training_csv(request):

    form, date_from, date_to = (
        get_report_dates(
            request
        )
    )

    if not form.is_valid():

        return HttpResponseBadRequest(
            "Invalid report date range."
        )


    assignments = (
        EmployeeTraining.objects
        .select_related(
            "user",
            "training",
        )
        .prefetch_related(
            "quiz_attempts"
        )
        .order_by(
            "-assigned_at"
        )
    )


    if date_from:

        assignments = assignments.filter(
            assigned_at__date__gte=(
                date_from
            )
        )


    if date_to:

        assignments = assignments.filter(
            assigned_at__date__lte=(
                date_to
            )
        )


    response = HttpResponse(
        content_type=(
            "text/csv; charset=utf-8"
        )
    )

    response[
        "Content-Disposition"
    ] = (
        'attachment; '
        'filename="lakdiva_training_report.csv"'
    )


    writer = csv.writer(
        response
    )

    writer.writerow(
        [
            "Staff No",
            "Employee",
            "Training",
            "Assigned At",
            "Due Date",
            "Progress %",
            "Training Status",
            "Latest Quiz %",
            "Quiz Result",
        ]
    )


    for assignment in assignments:

        attempts = list(
            assignment
            .quiz_attempts
            .all()
        )


        latest_attempt = None

        if attempts:

            latest_attempt = max(
                attempts,
                key=lambda attempt:
                    attempt.attempt_number,
            )


        writer.writerow(
            [
                safe_csv_value(
                    assignment.user.staff_no
                ),

                safe_csv_value(
                    assignment.user.full_name
                ),

                safe_csv_value(
                    assignment.training.title
                ),

                assignment.assigned_at,

                assignment.due_date
                or "",

                assignment.progress_percent,

                assignment.status,

                (
                    latest_attempt.percentage
                    if latest_attempt
                    else ""
                ),

                (
                    "PASS"
                    if (
                        latest_attempt
                        and
                        latest_attempt.passed
                    )
                    else (
                        "NOT PASSED"
                        if latest_attempt
                        else ""
                    )
                ),
            ]
        )


    log_action(
        request=request,
        action="REPORT_GENERATED",
        entity_type="TrainingReport",
        entity_id=None,
        details=(
            "Administrator generated "
            "the training report."
        ),
    )

    return response


# =========================================================
# POS SECURITY CSV REPORT
# =========================================================

@role_required(Role.ADMIN)
def pos_csv(request):

    form, date_from, date_to = (
        get_report_dates(
            request
        )
    )

    if not form.is_valid():

        return HttpResponseBadRequest(
            "Invalid report date range."
        )


    shifts = (
        POSShift.objects
        .select_related(
            "user",
            "pos",
            "handed_over_to",
            "security_check",
        )
        .order_by(
            "-shift_start"
        )
    )


    if date_from:

        shifts = shifts.filter(
            shift_start__date__gte=(
                date_from
            )
        )


    if date_to:

        shifts = shifts.filter(
            shift_start__date__lte=(
                date_to
            )
        )


    response = HttpResponse(
        content_type=(
            "text/csv; charset=utf-8"
        )
    )

    response[
        "Content-Disposition"
    ] = (
        'attachment; '
        'filename="lakdiva_pos_security_report.csv"'
    )


    writer = csv.writer(
        response
    )

    writer.writerow(
        [
            "Shift ID",
            "Staff No",
            "Employee",
            "POS",
            "Shift Start",
            "Shift End",
            "Status",
            "Opening Cash",
            "Cash In",
            "Cash Out",
            "Closing Cash",
            "Cash Variance",
            "Security Check",
            "Security Result",
        ]
    )


    for shift in shifts:

        security_check = getattr(
            shift,
            "security_check",
            None,
        )


        writer.writerow(
            [
                shift.shift_id,

                safe_csv_value(
                    shift.user.staff_no
                ),

                safe_csv_value(
                    shift.user.full_name
                ),

                safe_csv_value(
                    shift.pos.terminal_code
                ),

                shift.shift_start,

                shift.shift_end
                or "",

                shift.status,

                shift.opening_cash,

                shift.cash_in,

                shift.cash_out,

                shift.closing_cash
                if (
                    shift.closing_cash
                    is not None
                )
                else "",

                shift.cash_variance
                if (
                    shift.cash_variance
                    is not None
                )
                else "",

                (
                    "Completed"
                    if security_check
                    else "Not Completed"
                ),

                (
                    security_check.result
                    if security_check
                    else ""
                ),
            ]
        )


    log_action(
        request=request,
        action="REPORT_GENERATED",
        entity_type="POSSecurityReport",
        entity_id=None,
        details=(
            "Administrator generated "
            "the POS security report."
        ),
    )

    return response


# =========================================================
# INCIDENT CSV REPORT
# =========================================================

@role_required(Role.ADMIN)
def incident_csv(request):

    form, date_from, date_to = (
        get_report_dates(
            request
        )
    )

    if not form.is_valid():

        return HttpResponseBadRequest(
            "Invalid report date range."
        )


    latest_risk_level = (
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


    latest_risk_score = (
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
            "risk_score"
        )[:1]
    )


    incidents = (
        Incident.objects
        .select_related(
            "reported_by",
            "category",
            "pos",
        )
        .annotate(
            current_risk_level=(
                Subquery(
                    latest_risk_level
                )
            ),

            current_risk_score=(
                Subquery(
                    latest_risk_score
                )
            ),
        )
        .order_by(
            "-created_at"
        )
    )


    if date_from:

        incidents = incidents.filter(
            created_at__date__gte=(
                date_from
            )
        )


    if date_to:

        incidents = incidents.filter(
            created_at__date__lte=(
                date_to
            )
        )


    response = HttpResponse(
        content_type=(
            "text/csv; charset=utf-8"
        )
    )

    response[
        "Content-Disposition"
    ] = (
        'attachment; '
        'filename="lakdiva_incident_report.csv"'
    )


    writer = csv.writer(
        response
    )

    writer.writerow(
        [
            "Incident Reference",
            "Title",
            "Category",
            "Reported By",
            "POS",
            "Status",
            "Risk Score",
            "Risk Level",
            "Reported At",
            "Resolved At",
        ]
    )


    for incident in incidents:

        writer.writerow(
            [
                safe_csv_value(
                    incident.incident_ref
                ),

                safe_csv_value(
                    incident.title
                ),

                safe_csv_value(
                    incident
                    .category
                    .category_name
                ),

                safe_csv_value(
                    incident
                    .reported_by
                    .staff_no
                ),

                (
                    safe_csv_value(
                        incident
                        .pos
                        .terminal_code
                    )
                    if incident.pos
                    else ""
                ),

                incident.status,

                (
                    incident
                    .current_risk_score
                    if (
                        incident
                        .current_risk_score
                        is not None
                    )
                    else ""
                ),

                incident.current_risk_level
                or "",

                incident.created_at,

                incident.resolved_at
                or "",
            ]
        )


    log_action(
        request=request,
        action="REPORT_GENERATED",
        entity_type="IncidentReport",
        entity_id=None,
        details=(
            "Administrator generated "
            "the security incident report."
        ),
    )

    return response