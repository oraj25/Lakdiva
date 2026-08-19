from django.contrib import messages

from django.db.models import Q

from django.shortcuts import (
    get_object_or_404,
    redirect,
    render,
)

from django.views.decorators.http import (
    require_POST,
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

from training.models import (
    EmployeeTraining,
)

from .forms import (
    AdditionalTrainingAssignmentForm,
)

from .models import (
    TrainingNeed,
)

from .services import (
    analyze_training_needs,
)


# =========================================================
# ADMIN - TRAINING NEED LIST
# =========================================================

@role_required(Role.ADMIN)
def admin_training_need_list(
    request,
):

    needs = (
        TrainingNeed.objects
        .select_related(
            "user",
            "training",
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

    priority = (
        request.GET
        .get(
            "priority",
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

        needs = needs.filter(

            Q(
                user__staff_no__icontains=(
                    search
                )
            )

            |

            Q(
                user__full_name__icontains=(
                    search
                )
            )

            |

            Q(
                training__title__icontains=(
                    search
                )
            )
        )


    if priority:

        needs = needs.filter(
            priority=priority
        )


    if status:

        needs = needs.filter(
            status=status
        )


    # -----------------------------------------------------
    # FIND ADDITIONAL ASSIGNMENT
    # -----------------------------------------------------

    for need in needs:

        need.additional_assignment = (
            EmployeeTraining.objects
            .filter(
                user=need.user,
                training=need.training,
                assigned_at__gte=(
                    need.identified_at
                ),
            )
            .order_by(
                "-assigned_at"
            )
            .first()
        )


    open_count = (
        TrainingNeed.objects.filter(
            status=(
                TrainingNeed
                .Status
                .OPEN
            )
        ).count()
    )

    high_count = (
        TrainingNeed.objects.filter(
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
        ).count()
    )


    return render(
        request,
        (
            "administrator/"
            "training_needs/list.html"
        ),
        {
            "needs": needs,

            "search": search,

            "selected_priority": (
                priority
            ),

            "selected_status": status,

            "priorities": (
                TrainingNeed
                .Priority
                .choices
            ),

            "statuses": (
                TrainingNeed
                .Status
                .choices
            ),

            "open_count": (
                open_count
            ),

            "high_count": (
                high_count
            ),
        },
    )


# =========================================================
# ADMIN - ANALYZE TRAINING RESULTS
# =========================================================

@role_required(Role.ADMIN)
@require_POST
def admin_analyze_training_needs(
    request,
):

    result = (
        analyze_training_needs()
    )


    log_action(
        request=request,

        action=(
            "TRAINING_NEEDS_ANALYZED"
        ),

        entity_type=(
            "TrainingNeed"
        ),

        entity_id=None,

        details=(
            f"Training-needs analysis "
            f"completed. "
            f"Created: "
            f"{result['created']}, "
            f"Updated: "
            f"{result['updated']}, "
            f"Addressed: "
            f"{result['addressed']}."
        ),
    )


    messages.success(
        request,
        (
            "Training-needs analysis completed. "
            f"Created: {result['created']}, "
            f"Updated: {result['updated']}, "
            f"Addressed: {result['addressed']}."
        ),
    )


    return redirect(
        "training_needs:admin_list"
    )


# =========================================================
# ADMIN - ASSIGN ADDITIONAL TRAINING
# =========================================================

@role_required(Role.ADMIN)
def admin_assign_training(
    request,
    need_id,
):

    need = get_object_or_404(
        TrainingNeed.objects
        .select_related(
            "user",
            "training",
        ),
        need_id=need_id,
        status=(
            TrainingNeed
            .Status
            .OPEN
        ),
    )


    form = (
        AdditionalTrainingAssignmentForm(
            request.POST or None
        )
    )


    if (
        request.method == "POST"
        and form.is_valid()
    ):

        # -------------------------------------------------
        # PREVENT DUPLICATE ACTIVE ASSIGNMENTS
        # -------------------------------------------------

        active_assignment = (
            EmployeeTraining.objects
            .filter(
                user=need.user,
                training=need.training,
            )
            .exclude(
                status=(
                    EmployeeTraining
                    .Status
                    .COMPLETED
                )
            )
            .exists()
        )


        if active_assignment:

            messages.error(
                request,
                (
                    "This employee already "
                    "has an unfinished assignment "
                    "for this training module."
                ),
            )

            return redirect(
                "training_needs:admin_list"
            )


        # -------------------------------------------------
        # CREATE ADDITIONAL ASSIGNMENT
        # -------------------------------------------------

        assignment = (
            EmployeeTraining.objects
            .create(
                user=need.user,
                training=need.training,
                assigned_by=request.user,
                due_date=(
                    form.cleaned_data[
                        "due_date"
                    ]
                ),
                status=(
                    EmployeeTraining
                    .Status
                    .ASSIGNED
                ),
                progress_percent=0,
            )
        )


        # -------------------------------------------------
        # NOTIFICATION
        # -------------------------------------------------

        Notification.objects.create(
            user=need.user,

            title=(
                "Additional Security Training"
            ),

            message=(
                f"Additional training "
                f"'{need.training.title}' "
                f"has been assigned based "
                f"on your training needs."
            ),

            notification_type=(
                Notification
                .NotificationType
                .TRAINING
            ),
        )


        # -------------------------------------------------
        # AUDIT
        # -------------------------------------------------

        log_action(
            request=request,

            action=(
                "ADDITIONAL_TRAINING_ASSIGNED"
            ),

            entity_type=(
                "EmployeeTraining"
            ),

            entity_id=(
                assignment
                .employee_training_id
            ),

            details=(
                f"Administrator "
                f"{request.user.staff_no} "
                f"assigned additional "
                f"'{need.training.title}' "
                f"training to "
                f"{need.user.staff_no} "
                f"for training need "
                f"{need.need_id}."
            ),
        )


        messages.success(
            request,
            (
                "Additional security training "
                "assigned successfully."
            ),
        )


        return redirect(
            "training_needs:admin_list"
        )


    return render(
        request,
        (
            "administrator/"
            "training_needs/assign.html"
        ),
        {
            "need": need,
            "form": form,
        },
    )