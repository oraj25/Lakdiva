from decimal import (
    Decimal,
    ROUND_HALF_UP,
)

from django.utils import timezone

from accounts.models import (
    Role,
    User,
)

from policies.models import (
    Policy,
    PolicyAcknowledgement,
)

from training.models import (
    EmployeeTraining,
)

from pos_security.models import (
    DailySecurityCheck,
    POSShift,
)

from notifications.models import (
    Notification,
)

from notifications.utils import (
    create_notification,
)

from .models import (
    ComplianceSummary,
)


# =========================================================
# HELPERS
# =========================================================

def calculate_percentage(
    completed,
    total,
):

    if total == 0:

        return Decimal("100.00")

    percentage = (
        Decimal(completed)
        /
        Decimal(total)
        *
        Decimal("100")
    )

    return percentage.quantize(
        Decimal("0.01"),
        rounding=ROUND_HALF_UP,
    )


# =========================================================
# USER COMPLIANCE CALCULATION
# =========================================================

def calculate_user_compliance(
    user,
):

    # =====================================================
    # POLICY COMPLIANCE
    # =====================================================

    published_policies = (
        Policy.objects.filter(
            status=Policy.Status.PUBLISHED
        )
    )

    total_policies = (
        published_policies.count()
    )

    acknowledged_policies = (
        PolicyAcknowledgement.objects
        .filter(
            user=user,
            policy__status=(
                Policy.Status.PUBLISHED
            ),
        )
        .values(
            "policy_id"
        )
        .distinct()
        .count()
    )

    policy_compliance = (
        calculate_percentage(
            acknowledged_policies,
            total_policies,
        )
    )


    # =====================================================
    # TRAINING COMPLIANCE
    # =====================================================

    assignments = list(
        EmployeeTraining.objects
        .filter(
            user=user
        )
        .select_related(
            "training"
        )
        .prefetch_related(
            "quiz_attempts",
            "training__quiz_questions",
        )
    )

    total_training = len(
        assignments
    )

    completed_training = sum(

        1

        for assignment
        in assignments

        if (
            assignment.status
            ==
            EmployeeTraining
            .Status
            .COMPLETED
        )
    )

    training_compliance = (
        calculate_percentage(
            completed_training,
            total_training,
        )
    )


    # =====================================================
    # QUIZ PERFORMANCE
    # =====================================================

    quiz_scores = []

    for assignment in assignments:

        questions = list(
            assignment
            .training
            .quiz_questions
            .all()
        )

        # Training has no quiz.
        if not questions:
            continue

        attempts = list(
            assignment
            .quiz_attempts
            .all()
        )

        if not attempts:

            quiz_scores.append(
                Decimal("0.00")
            )

            continue

        latest_attempt = max(
            attempts,
            key=lambda attempt:
                attempt.attempt_number,
        )

        quiz_scores.append(
            Decimal(
                str(
                    latest_attempt
                    .percentage
                )
            )
        )


    if quiz_scores:

        quiz_performance = (
            sum(
                quiz_scores,
                Decimal("0")
            )
            /
            Decimal(
                len(quiz_scores)
            )
        ).quantize(
            Decimal("0.01"),
            rounding=ROUND_HALF_UP,
        )

    else:

        quiz_performance = (
            Decimal("100.00")
        )


    # =====================================================
    # POS SECURITY CHECK COMPLIANCE
    # =====================================================

    total_shifts = (
        POSShift.objects
        .filter(
            user=user
        )
        .count()
    )

    completed_checks = (
        DailySecurityCheck.objects
        .filter(
            shift__user=user
        )
        .count()
    )

    pos_check_compliance = (
        calculate_percentage(
            completed_checks,
            total_shifts,
        )
    )


    # =====================================================
    # OVERALL EMPLOYEE SCORE
    # =====================================================

    # Policy      = 25%
    # Training    = 25%
    # Quiz        = 25%
    # POS Checks  = 25%

    employee_score = (
        (
            policy_compliance
            +
            training_compliance
            +
            quiz_performance
            +
            pos_check_compliance
        )
        /
        Decimal("4")
    ).quantize(
        Decimal("0.01"),
        rounding=ROUND_HALF_UP,
    )


    # =====================================================
    # SAVE SUMMARY
    # =====================================================

    summary, created = (
        ComplianceSummary.objects
        .update_or_create(

            user=user,

            defaults={

                "policy_compliance": (
                    policy_compliance
                ),

                "training_compliance": (
                    training_compliance
                ),

                "pos_check_compliance": (
                    pos_check_compliance
                ),

                "employee_score": (
                    employee_score
                ),

                "last_calculated_at": (
                    timezone.now()
                ),
            },
        )
    )


    # Not stored separately in the ERD,
    # but useful when the result is calculated.

    summary.quiz_performance = (
        quiz_performance
    )


    # =====================================================
    # COMPLIANCE WARNING
    # =====================================================

    compliance_warning_title = (
        "Compliance Attention Required"
    )

    compliance_threshold = (
        Decimal("70.00")
    )


    if employee_score < compliance_threshold:

        # -------------------------------------------------
        # CHECK FOR EXISTING UNREAD WARNING
        # -------------------------------------------------

        existing_warning = (
            Notification.objects
            .filter(
                user=user,

                notification_type=(
                    Notification
                    .NotificationType
                    .COMPLIANCE
                ),

                title=(
                    compliance_warning_title
                ),

                is_read=False,
            )
            .exists()
        )


        # -------------------------------------------------
        # CREATE WARNING ONLY IF ONE DOES NOT EXIST
        # -------------------------------------------------

        if not existing_warning:

            create_notification(
                user=user,

                title=(
                    compliance_warning_title
                ),

                message=(
                    f"Your current security "
                    f"compliance score is "
                    f"{employee_score}%. "
                    f"Please review outstanding "
                    f"policies, training and "
                    f"POS security requirements."
                ),

                notification_type=(
                    Notification
                    .NotificationType
                    .COMPLIANCE
                ),
            )


    else:

        # -------------------------------------------------
        # COMPLIANCE HAS IMPROVED
        # -------------------------------------------------
        #
        # The employee is no longer below the
        # threshold, so old unread compliance
        # warnings should no longer remain active.
        # -------------------------------------------------

        Notification.objects.filter(
            user=user,

            notification_type=(
                Notification
                .NotificationType
                .COMPLIANCE
            ),

            title=(
                compliance_warning_title
            ),

            is_read=False,
        ).update(
            is_read=True,
            read_at=timezone.now(),
        )


    return summary


# =========================================================
# RECALCULATE ALL ACTIVE EMPLOYEES
# =========================================================

def recalculate_all_employee_compliance():

    employees = (
        User.objects.filter(
            role__role_name=(
                Role.EMPLOYEE
            ),
            status=User.Status.ACTIVE,
        )
    )

    updated_count = 0

    for employee in employees:

        calculate_user_compliance(
            employee
        )

        updated_count += 1

    return updated_count