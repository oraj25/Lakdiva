import os
import uuid

from pathlib import Path

from django.contrib import messages

from django.contrib.auth.decorators import (
    login_required,
)

from django.db import transaction

from django.db.models import (
    OuterRef,
    Q,
    Subquery,
)

from django.http import (
    FileResponse,
    Http404,
)

from django.shortcuts import (
    get_object_or_404,
    redirect,
    render,
)

from accounts.decorators import (
    role_required,
)

from accounts.models import (
    Role,
)

from auditlog.utils import (
    log_action,
)

from notifications.models import (
    Notification,
)

from notifications.utils import (
    notify_active_admins,
)

from pos_security.models import (
    POSShift,
)

from .forms import (
    IncidentReportForm,
    IncidentRiskAssessmentForm,
)

from .models import (
    Incident,
    IncidentCategory,
    IncidentEvidence,
    IncidentRiskAssessment,
)


# =========================================================
# HELPERS
# =========================================================

def classify_evidence_file(
    filename,
):

    extension = (
        Path(
            filename
        )
        .suffix
        .lower()
    )

    if extension in {
        ".jpg",
        ".jpeg",
        ".png",
    }:

        return (
            IncidentEvidence
            .FileType
            .IMAGE
        )

    if extension == ".pdf":

        return (
            IncidentEvidence
            .FileType
            .DOCUMENT
        )

    if extension in {
        ".txt",
        ".log",
    }:

        return (
            IncidentEvidence
            .FileType
            .LOG
        )

    return (
        IncidentEvidence
        .FileType
        .OTHER
    )


# =========================================================
# EMPLOYEE - INCIDENT LIST
# =========================================================

@role_required(Role.EMPLOYEE)
def employee_incident_list(
    request,
):

    incidents = (
        Incident.objects
        .filter(
            reported_by=request.user
        )
        .select_related(
            "category",
            "pos",
        )
    )

    search = (
        request.GET
        .get(
            "search",
            "",
        )
        .strip()
    )

    status = (
        request.GET
        .get(
            "status",
            "",
        )
        .strip()
    )

    if search:

        incidents = incidents.filter(
            Q(
                incident_ref__icontains=search
            )
            |
            Q(
                title__icontains=search
            )
            |
            Q(
                category__category_name__icontains=search
            )
        )

    if status:

        incidents = incidents.filter(
            status=status
        )

    return render(
        request,
        "employee/incidents/list.html",
        {
            "incidents": incidents,
            "search": search,
            "selected_status": status,
            "statuses": (
                Incident.Status.choices
            ),
        },
    )


# =========================================================
# EMPLOYEE - REPORT INCIDENT
# =========================================================

@role_required(Role.EMPLOYEE)
def employee_incident_create(
    request,
):

    initial = {}

    # -----------------------------------------------------
    # OPTIONAL POS SHIFT PREFILL
    # -----------------------------------------------------

    shift_id = (
        request.GET.get(
            "shift"
        )
    )

    if (
        request.method == "GET"
        and shift_id
    ):

        shift = (
            POSShift.objects
            .filter(
                shift_id=shift_id,
                user=request.user,
            )
            .select_related(
                "pos"
            )
            .first()
        )

        if shift:

            initial[
                "shift"
            ] = shift

            initial[
                "pos"
            ] = shift.pos

    form = IncidentReportForm(
        request.POST or None,
        request.FILES or None,
        user=request.user,
        initial=initial,
    )

    if (
        request.method == "POST"
        and form.is_valid()
    ):

        evidence_files = (
            form.cleaned_data.get(
                "evidence"
            )
            or []
        )

        with transaction.atomic():

            incident = form.save(
                commit=False
            )

            incident.reported_by = (
                request.user
            )

            incident.status = (
                Incident.Status.NEW
            )

            # If incident came from a POS shift,
            # always use the POS attached to
            # that shift.
            if incident.shift_id:

                incident.pos = (
                    incident.shift.pos
                )

            # Temporary unique value so
            # the initial INSERT can occur.
            incident.incident_ref = (
                "TEMP-"
                + uuid.uuid4().hex
            )

            incident.save()

            # Final human-readable reference.
            incident.incident_ref = (
                f"INC-"
                f"{incident.incident_id:06d}"
            )

            incident.save(
                update_fields=[
                    "incident_ref"
                ]
            )

            # ---------------------------------------------
            # SAVE EVIDENCE
            # ---------------------------------------------

            for uploaded_file in evidence_files:

                IncidentEvidence.objects.create(
                    incident=incident,
                    file=uploaded_file,
                    file_type=(
                        classify_evidence_file(
                            uploaded_file.name
                        )
                    ),
                    uploaded_by=(
                        request.user
                    ),
                )

            # ---------------------------------------------
            # ADMIN NOTIFICATIONS
            # ---------------------------------------------

            notify_active_admins(
                title=(
                    "New Security Incident"
                ),
                message=(
                    f"{incident.incident_ref} "
                    f"was reported by "
                    f"{request.user.staff_no}. "
                    f"Category: "
                    f"{incident.category.category_name}."
                ),
                notification_type=(
                    Notification
                    .NotificationType
                    .NEW_INCIDENT
                ),
            )

        # -------------------------------------------------
        # AUDIT
        # -------------------------------------------------

        log_action(
            request=request,
            action="INCIDENT_REPORTED",
            entity_type="Incident",
            entity_id=(
                incident.incident_id
            ),
            details=(
                f"Employee "
                f"{request.user.staff_no} "
                f"reported incident "
                f"{incident.incident_ref}. "
                f"Category: "
                f"{incident.category.category_name}."
            ),
        )

        messages.success(
            request,
            (
                "Security incident reported "
                "successfully. Reference: "
                f"{incident.incident_ref}"
            ),
        )

        return redirect(
            "incidents:employee_detail",
            incident_id=(
                incident.incident_id
            ),
        )

    return render(
        request,
        (
            "employee/"
            "incidents/report.html"
        ),
        {
            "form": form,
        },
    )


# =========================================================
# EMPLOYEE - INCIDENT DETAIL
# =========================================================

@role_required(Role.EMPLOYEE)
def employee_incident_detail(
    request,
    incident_id,
):

    incident = get_object_or_404(
        Incident.objects
        .select_related(
            "category",
            "pos",
            "shift",
        )
        .prefetch_related(
            "evidence_files"
        ),
        incident_id=incident_id,
        reported_by=request.user,
    )

    return render(
        request,
        (
            "employee/"
            "incidents/detail.html"
        ),
        {
            "incident": incident,
        },
    )


# =========================================================
# SECURE EVIDENCE DOWNLOAD
# =========================================================

@login_required
def evidence_download(
    request,
    evidence_id,
):

    base_queryset = (
        IncidentEvidence.objects
        .select_related(
            "incident",
            "incident__reported_by",
        )
    )

    role = getattr(
        request.user,
        "role",
        None,
    )

    if not role:

        raise Http404

    if (
        role.role_name
        == Role.ADMIN
    ):

        evidence = (
            get_object_or_404(
                base_queryset,
                evidence_id=evidence_id,
            )
        )

    elif (
        role.role_name
        == Role.EMPLOYEE
    ):

        evidence = (
            get_object_or_404(
                base_queryset,
                evidence_id=evidence_id,
                incident__reported_by=(
                    request.user
                ),
            )
        )

    else:

        raise Http404

    if not evidence.file:

        raise Http404

    try:

        file_handle = (
            evidence.file.open(
                "rb"
            )
        )

    except FileNotFoundError:

        raise Http404

    filename = os.path.basename(
        evidence.file.name
    )

    return FileResponse(
        file_handle,
        as_attachment=True,
        filename=filename,
    )


# =========================================================
# ADMIN - INCIDENT LIST
# =========================================================

@role_required(Role.ADMIN)
def admin_incident_list(
    request,
):

    latest_risk_level_query = (
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


    latest_risk_score_query = (
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
            latest_risk_level=(
                Subquery(
                    latest_risk_level_query
                )
            ),

            latest_risk_score=(
                Subquery(
                    latest_risk_score_query
                )
            ),
        )
        .all()
    )

    search = (
        request.GET
        .get(
            "search",
            "",
        )
        .strip()
    )

    status = (
        request.GET
        .get(
            "status",
            "",
        )
        .strip()
    )

    category_id = (
        request.GET
        .get(
            "category",
            "",
        )
        .strip()
    )

    if search:

        incidents = incidents.filter(
            Q(
                incident_ref__icontains=search
            )
            |
            Q(
                title__icontains=search
            )
            |
            Q(
                reported_by__staff_no__icontains=search
            )
            |
            Q(
                reported_by__full_name__icontains=search
            )
        )

    if status:

        incidents = incidents.filter(
            status=status
        )

    if category_id:

        incidents = incidents.filter(
            category_id=category_id
        )

    categories = (
        IncidentCategory.objects
        .filter(
            status=(
                IncidentCategory
                .Status
                .ACTIVE
            )
        )
    )

    return render(
        request,
        (
            "administrator/"
            "incidents/list.html"
        ),
        {
            "incidents": incidents,
            "categories": categories,
            "search": search,
            "selected_status": status,
            "selected_category": (
                category_id
            ),
            "statuses": (
                Incident.Status.choices
            ),
        },
    )


# =========================================================
# ADMIN - INCIDENT DETAIL
# =========================================================

@role_required(Role.ADMIN)
def admin_incident_detail(
    request,
    incident_id,
):

    incident = get_object_or_404(
        Incident.objects
        .select_related(
            "reported_by",
            "category",
            "pos",
            "shift",
        )
        .prefetch_related(
            "evidence_files"
        ),
        incident_id=incident_id,
    )


    risk_assessments = (
        IncidentRiskAssessment
        .objects
        .filter(
            incident=incident
        )
        .select_related(
            "assessed_by"
        )
        .order_by(
            "-assessed_at"
        )
    )


    latest_risk = (
        risk_assessments.first()
    )


    return render(
        request,
        (
            "administrator/"
            "incidents/detail.html"
        ),
        {
            "incident": incident,

            "risk_assessments": (
                risk_assessments
            ),

            "latest_risk": (
                latest_risk
            ),
        },
    )

# =========================================================
# ADMIN - INCIDENT RISK ASSESSMENT
# =========================================================

@role_required(Role.ADMIN)
def admin_risk_assessment_create(
    request,
    incident_id,
):

    incident = get_object_or_404(
        Incident.objects
        .select_related(
            "reported_by",
            "category",
            "pos",
            "shift",
        )
        .prefetch_related(
            "evidence_files"
        ),
        incident_id=incident_id,
    )


    # -----------------------------------------------------
    # PREVIOUS ASSESSMENT
    # -----------------------------------------------------

    previous_assessment = (
        IncidentRiskAssessment
        .objects
        .filter(
            incident=incident
        )
        .order_by(
            "-assessed_at"
        )
        .first()
    )


    # -----------------------------------------------------
    # INITIAL VALUES
    # -----------------------------------------------------

    initial = {}

    if request.method == "GET":

        if previous_assessment:

            initial = {

                "customer_data_involved": (
                    previous_assessment
                    .customer_data_involved
                ),

                "pos_affected": (
                    previous_assessment
                    .pos_affected
                ),

                "unauthorized_access": (
                    previous_assessment
                    .unauthorized_access
                ),

                "business_impact": (
                    previous_assessment
                    .business_impact
                ),
            }

        else:

            # If a POS is already linked,
            # suggest POS affected = Yes.
            initial = {

                "customer_data_involved": (
                    False
                ),

                "pos_affected": bool(
                    incident.pos_id
                ),

                "unauthorized_access": (
                    False
                ),

                "business_impact": 0,
            }


    form = (
        IncidentRiskAssessmentForm(
            request.POST or None,
            initial=initial,
        )
    )


    # -----------------------------------------------------
    # SUBMIT ASSESSMENT
    # -----------------------------------------------------

    if (
        request.method == "POST"
        and form.is_valid()
    ):

        evidence_available = (
            incident.evidence_files
            .exists()
        )

        with transaction.atomic():

            assessment = form.save(
                commit=False
            )

            assessment.incident = (
                incident
            )

            assessment.assessed_by = (
                request.user
            )

            assessment.evidence_available = (
                evidence_available
            )

            # Risk score and level are
            # automatically calculated
            # inside model.save().
            assessment.save()


            # ---------------------------------------------
            # HIGH-RISK NOTIFICATION
            # ---------------------------------------------

            was_previously_high = (
                previous_assessment
                and
                previous_assessment
                .risk_level
                ==
                IncidentRiskAssessment
                .RiskLevel
                .HIGH
            )

            if (
                assessment.risk_level
                ==
                IncidentRiskAssessment
                .RiskLevel
                .HIGH
                and
                not was_previously_high
            ):

                notify_active_admins(
                    title=(
                        "High-Risk Incident "
                        "Identified"
                    ),
                    message=(
                        f"{incident.incident_ref} "
                        f"has been classified "
                        f"HIGH risk with a score "
                        f"of "
                        f"{assessment.risk_score}"
                        f"/12."
                    ),
                    notification_type=(
                        Notification
                        .NotificationType
                        .HIGH_RISK_INCIDENT
                    ),
                )


        # -------------------------------------------------
        # AUDIT LOG
        # -------------------------------------------------

        log_action(
            request=request,
            action=(
                "INCIDENT_RISK_ASSESSED"
            ),
            entity_type=(
                "IncidentRiskAssessment"
            ),
            entity_id=(
                assessment.risk_id
            ),
            details=(
                f"Administrator "
                f"{request.user.staff_no} "
                f"assessed "
                f"{incident.incident_ref}. "
                f"Risk score: "
                f"{assessment.risk_score}/12. "
                f"Risk level: "
                f"{assessment.risk_level}."
            ),
        )


        # -------------------------------------------------
        # MESSAGE
        # -------------------------------------------------

        if (
            assessment.risk_level
            ==
            IncidentRiskAssessment
            .RiskLevel
            .HIGH
        ):

            messages.warning(
                request,
                (
                    f"{incident.incident_ref} "
                    f"has been classified "
                    f"HIGH RISK "
                    f"({assessment.risk_score}/12)."
                ),
            )

        else:

            messages.success(
                request,
                (
                    "Risk assessment completed. "
                    f"Risk level: "
                    f"{assessment.risk_level} "
                    f"({assessment.risk_score}/12)."
                ),
            )


        return redirect(
            "incidents:admin_detail",
            incident_id=(
                incident.incident_id
            ),
        )


    # -----------------------------------------------------
    # DISPLAY FORM
    # -----------------------------------------------------

    return render(
        request,
        (
            "administrator/"
            "incidents/"
            "risk_assessment.html"
        ),
        {
            "incident": incident,

            "form": form,

            "previous_assessment": (
                previous_assessment
            ),

            "evidence_available": (
                incident.evidence_files
                .exists()
            ),
        },
    )