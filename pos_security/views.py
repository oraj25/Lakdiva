from decimal import Decimal

from django.contrib import messages

from django.db import transaction

from django.db.models import Q

from django.shortcuts import (
    get_object_or_404,
    redirect,
    render,
)

from django.utils import timezone

from django.views.decorators.http import (
    require_POST,
)

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

from .forms import (
    CashUpdateForm,
    CloseShiftForm,
    DailySecurityCheckForm,
    StartShiftForm,
)

from .models import (
    DailySecurityCheck,
    POSTerminal,
    POSShift,
)


# =========================================================
# EMPLOYEE - POS HOME
# =========================================================

@role_required(Role.EMPLOYEE)
def employee_pos_list(request):

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

    recent_shifts = (
        POSShift.objects
        .filter(
            user=request.user
        )
        .select_related(
            "pos",
            "handed_over_to",
        )[:10]
    )

    return render(
        request,
        "employee/pos/list.html",
        {
            "open_shift": open_shift,
            "recent_shifts": recent_shifts,
        },
    )


# =========================================================
# EMPLOYEE - START SHIFT
# =========================================================

@role_required(Role.EMPLOYEE)
def employee_shift_start(request):

    if POSShift.objects.filter(
        user=request.user,
        status=POSShift.Status.OPEN,
    ).exists():

        messages.error(
            request,
            (
                "You already have an "
                "open POS shift."
            ),
        )

        return redirect(
            "pos_security:employee_list"
        )

    form = StartShiftForm(
        request.POST or None
    )

    if (
        request.method == "POST"
        and form.is_valid()
    ):

        selected_pos = (
            form.cleaned_data["pos"]
        )

        opening_cash = (
            form.cleaned_data[
                "opening_cash"
            ]
        )

        with transaction.atomic():

            # Lock the employee row.
            User.objects.select_for_update().get(
                user_id=request.user.user_id
            )

            # Lock the selected POS row.
            terminal = (
                POSTerminal.objects
                .select_for_update()
                .get(
                    pos_id=(
                        selected_pos.pos_id
                    ),
                    status=(
                        POSTerminal
                        .Status
                        .ACTIVE
                    ),
                )
            )

            # Recheck employee after lock.
            if POSShift.objects.filter(
                user=request.user,
                status=(
                    POSShift.Status.OPEN
                ),
            ).exists():

                messages.error(
                    request,
                    (
                        "You already have "
                        "an open shift."
                    ),
                )

                return redirect(
                    "pos_security:"
                    "employee_list"
                )

            # Prevent two employees using
            # the same POS simultaneously.
            if POSShift.objects.filter(
                pos=terminal,
                status=(
                    POSShift.Status.OPEN
                ),
            ).exists():

                messages.error(
                    request,
                    (
                        f"{terminal.terminal_code} "
                        f"already has an "
                        f"open shift."
                    ),
                )

                return redirect(
                    "pos_security:"
                    "employee_shift_start"
                )

            shift = POSShift.objects.create(
                user=request.user,
                pos=terminal,
                opening_cash=opening_cash,
                cash_in=Decimal("0.00"),
                cash_out=Decimal("0.00"),
                status=(
                    POSShift.Status.OPEN
                ),
            )

        log_action(
            request=request,
            action="POS_SHIFT_STARTED",
            entity_type="POSShift",
            entity_id=shift.shift_id,
            details=(
                f"Employee "
                f"{request.user.staff_no} "
                f"started shift "
                f"{shift.shift_id} on "
                f"{shift.pos.terminal_code}."
            ),
        )

        messages.success(
            request,
            (
                "POS shift started "
                "successfully."
            ),
        )

        return redirect(
            "pos_security:employee_detail",
            shift_id=shift.shift_id,
        )

    return render(
        request,
        "employee/pos/start.html",
        {
            "form": form,
        },
    )


# =========================================================
# EMPLOYEE - SHIFT DETAIL
# =========================================================

@role_required(Role.EMPLOYEE)
def employee_shift_detail(
    request,
    shift_id,
):

    shift = get_object_or_404(
        POSShift.objects.select_related(
            "pos",
            "handed_over_to",
        ),
        shift_id=shift_id,
        user=request.user,
    )

    security_check = (
        DailySecurityCheck.objects
        .filter(
            shift=shift
        )
        .first()
    )

    return render(
        request,
        "employee/pos/detail.html",
        {
            "shift": shift,
            "security_check": (
                security_check
            ),
        },
    )


# =========================================================
# EMPLOYEE - UPDATE CASH
# =========================================================

@role_required(Role.EMPLOYEE)
def employee_cash_update(
    request,
    shift_id,
):

    shift = get_object_or_404(
        POSShift,
        shift_id=shift_id,
        user=request.user,
        status=POSShift.Status.OPEN,
    )

    form = CashUpdateForm(
        request.POST or None,
        instance=shift,
    )

    if (
        request.method == "POST"
        and form.is_valid()
    ):

        with transaction.atomic():

            locked_shift = (
                POSShift.objects
                .select_for_update()
                .get(
                    shift_id=shift.shift_id,
                    user=request.user,
                    status=(
                        POSShift.Status.OPEN
                    ),
                )
            )

            locked_shift.cash_in = (
                form.cleaned_data[
                    "cash_in"
                ]
            )

            locked_shift.cash_out = (
                form.cleaned_data[
                    "cash_out"
                ]
            )

            locked_shift.save(
                update_fields=[
                    "cash_in",
                    "cash_out",
                ]
            )

        log_action(
            request=request,
            action="POS_CASH_UPDATED",
            entity_type="POSShift",
            entity_id=shift.shift_id,
            details=(
                f"Cash totals updated for "
                f"shift {shift.shift_id}. "
                f"Cash in: "
                f"{locked_shift.cash_in}, "
                f"Cash out: "
                f"{locked_shift.cash_out}."
            ),
        )

        messages.success(
            request,
            "Cash totals updated.",
        )

        return redirect(
            "pos_security:employee_detail",
            shift_id=shift.shift_id,
        )

    return render(
        request,
        "employee/pos/cash_update.html",
        {
            "shift": shift,
            "form": form,
        },
    )


# =========================================================
# EMPLOYEE - SECURITY CHECK
# =========================================================

@role_required(Role.EMPLOYEE)
def employee_security_check(
    request,
    shift_id,
):

    shift = get_object_or_404(
        POSShift.objects.select_related(
            "pos"
        ),
        shift_id=shift_id,
        user=request.user,
        status=POSShift.Status.OPEN,
    )

    existing_check = (
        DailySecurityCheck.objects
        .filter(
            shift=shift
        )
        .first()
    )

    form = DailySecurityCheckForm(
        request.POST or None,
        instance=existing_check,
    )

    if (
        request.method == "POST"
        and form.is_valid()
    ):

        with transaction.atomic():

            locked_shift = (
                POSShift.objects
                .select_for_update()
                .get(
                    shift_id=shift.shift_id,
                    user=request.user,
                    status=(
                        POSShift.Status.OPEN
                    ),
                )
            )

            security_check = (
                form.save(
                    commit=False
                )
            )

            security_check.shift = (
                locked_shift
            )

            security_check.result = (
                security_check
                .calculate_result()
            )

            security_check.checked_at = (
                timezone.now()
            )

            security_check.save()

        log_action(
            request=request,
            action="POS_SECURITY_CHECK_COMPLETED",
            entity_type=(
                "DailySecurityCheck"
            ),
            entity_id=(
                security_check.check_id
            ),
            details=(
                f"Security check completed "
                f"for shift "
                f"{shift.shift_id}. "
                f"Result: "
                f"{security_check.result}."
            ),
        )

        if (
            security_check.result
            ==
            DailySecurityCheck
            .Result
            .SUSPICIOUS
        ):

            messages.warning(
                request,
                (
                    "Security concern detected. "
                    "This POS check has been "
                    "marked Suspicious."
                ),
            )

        else:

            messages.success(
                request,
                (
                    "Security check completed. "
                    "No security concerns "
                    "were identified."
                ),
            )

        return redirect(
            "pos_security:employee_detail",
            shift_id=shift.shift_id,
        )

    return render(
        request,
        (
            "employee/pos/"
            "security_check.html"
        ),
        {
            "shift": shift,
            "form": form,
            "existing_check": (
                existing_check
            ),
        },
    )


# =========================================================
# EMPLOYEE - CLOSE SHIFT / HANDOVER
# =========================================================

@role_required(Role.EMPLOYEE)
def employee_shift_close(
    request,
    shift_id,
):

    shift = get_object_or_404(
        POSShift.objects.select_related(
            "pos"
        ),
        shift_id=shift_id,
        user=request.user,
        status=POSShift.Status.OPEN,
    )

    # Security check required before close.
    if not DailySecurityCheck.objects.filter(
        shift=shift
    ).exists():

        messages.error(
            request,
            (
                "Complete the POS security "
                "check before ending the shift."
            ),
        )

        return redirect(
            "pos_security:"
            "employee_security_check",
            shift_id=shift.shift_id,
        )

    form = CloseShiftForm(
        request.POST or None,
        instance=shift,
        current_user=request.user,
    )

    if (
        request.method == "POST"
        and form.is_valid()
    ):

        with transaction.atomic():

            locked_shift = (
                POSShift.objects
                .select_for_update()
                .get(
                    shift_id=shift.shift_id,
                    user=request.user,
                    status=(
                        POSShift.Status.OPEN
                    ),
                )
            )

            closing_cash = (
                form.cleaned_data[
                    "closing_cash"
                ]
            )

            handed_over_to = (
                form.cleaned_data[
                    "handed_over_to"
                ]
            )

            handover_notes = (
                form.cleaned_data[
                    "handover_notes"
                ]
            )

            locked_shift.closing_cash = (
                closing_cash
            )

            locked_shift.handed_over_to = (
                handed_over_to
            )

            locked_shift.handover_notes = (
                handover_notes
            )

            if handed_over_to:

                locked_shift.handover_time = (
                    timezone.now()
                )

            locked_shift.cash_variance = (
                locked_shift
                .calculate_variance()
            )

            locked_shift.shift_end = (
                timezone.now()
            )

            locked_shift.status = (
                POSShift.Status.COMPLETED
            )

            locked_shift.save(
                update_fields=[
                    "closing_cash",
                    "cash_variance",
                    "handed_over_to",
                    "handover_time",
                    "handover_notes",
                    "shift_end",
                    "status",
                ]
            )

        log_action(
            request=request,
            action="POS_SHIFT_COMPLETED",
            entity_type="POSShift",
            entity_id=(
                locked_shift.shift_id
            ),
            details=(
                f"Employee "
                f"{request.user.staff_no} "
                f"completed shift "
                f"{locked_shift.shift_id}. "
                f"Cash variance: "
                f"{locked_shift.cash_variance}."
            ),
        )

        messages.success(
            request,
            (
                "POS shift completed "
                "successfully."
            ),
        )

        return redirect(
            "pos_security:employee_detail",
            shift_id=(
                locked_shift.shift_id
            ),
        )

    return render(
        request,
        "employee/pos/close.html",
        {
            "shift": shift,
            "form": form,
            "expected_cash": (
                shift.expected_cash
            ),
        },
    )


# =========================================================
# ADMIN - POS RECORD LIST
# =========================================================

@role_required(Role.ADMIN)
def admin_pos_list(request):

    shifts = (
        POSShift.objects
        .select_related(
            "user",
            "pos",
            "handed_over_to",
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

    pos_id = (
        request.GET
        .get(
            "pos",
            "",
        )
        .strip()
    )

    if search:

        shifts = shifts.filter(
            Q(
                user__staff_no__icontains=search
            )
            |
            Q(
                user__full_name__icontains=search
            )
            |
            Q(
                pos__terminal_code__icontains=search
            )
        )

    if status:

        shifts = shifts.filter(
            status=status
        )

    if pos_id:

        shifts = shifts.filter(
            pos_id=pos_id
        )

    terminals = (
        POSTerminal.objects.all()
    )

    return render(
        request,
        (
            "administrator/"
            "pos/list.html"
        ),
        {
            "shifts": shifts,
            "terminals": terminals,
            "search": search,
            "selected_status": status,
            "selected_pos": pos_id,
            "statuses": (
                POSShift.Status.choices
            ),
        },
    )


# =========================================================
# ADMIN - POS RECORD DETAIL
# =========================================================

@role_required(Role.ADMIN)
def admin_pos_detail(
    request,
    shift_id,
):

    shift = get_object_or_404(
        POSShift.objects
        .select_related(
            "user",
            "pos",
            "handed_over_to",
        ),
        shift_id=shift_id,
    )

    security_check = (
        DailySecurityCheck.objects
        .filter(
            shift=shift
        )
        .first()
    )

    return render(
        request,
        (
            "administrator/"
            "pos/detail.html"
        ),
        {
            "shift": shift,
            "security_check": (
                security_check
            ),
        },
    )