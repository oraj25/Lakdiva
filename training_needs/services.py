from decimal import Decimal

from django.conf import settings

from training.models import (
    EmployeeTraining,
    QuizAttempt,
)

from .models import (
    TrainingNeed,
)


# =========================================================
# SETTINGS
# =========================================================

def get_training_need_threshold():

    return Decimal(
        str(
            getattr(
                settings,
                "TRAINING_NEED_THRESHOLD",
                70,
            )
        )
    )


def get_high_threshold():

    return Decimal(
        str(
            getattr(
                settings,
                "TRAINING_NEED_HIGH_THRESHOLD",
                40,
            )
        )
    )


def get_medium_threshold():

    return Decimal(
        str(
            getattr(
                settings,
                "TRAINING_NEED_MEDIUM_THRESHOLD",
                60,
            )
        )
    )


# =========================================================
# PRIORITY CALCULATION
# =========================================================

def get_priority_for_score(
    score,
):

    score = Decimal(
        str(score)
    )

    if score < get_high_threshold():

        return (
            TrainingNeed
            .Priority
            .HIGH
        )

    if score < get_medium_threshold():

        return (
            TrainingNeed
            .Priority
            .MEDIUM
        )

    if (
        score
        <
        get_training_need_threshold()
    ):

        return (
            TrainingNeed
            .Priority
            .LOW
        )

    return None


# =========================================================
# CHECK ADDITIONAL TRAINING COMPLETION
# =========================================================

def address_completed_training_needs():

    addressed_count = 0

    open_needs = (
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
    )

    for need in open_needs:

        additional_training_completed = (
            EmployeeTraining.objects
            .filter(
                user=need.user,
                training=need.training,
                assigned_at__gte=(
                    need.identified_at
                ),
                status=(
                    EmployeeTraining
                    .Status
                    .COMPLETED
                ),
            )
            .exists()
        )

        if additional_training_completed:

            need.status = (
                TrainingNeed
                .Status
                .ADDRESSED
            )

            need.save(
                update_fields=[
                    "status"
                ]
            )

            addressed_count += 1

    return addressed_count


# =========================================================
# ANALYZE QUIZ RESULTS
# =========================================================

def analyze_training_needs():

    created_count = 0
    updated_count = 0
    addressed_count = 0

    # First check whether previously assigned
    # additional training has been completed.
    addressed_count += (
        address_completed_training_needs()
    )


    # -----------------------------------------------------
    # GET QUIZ ATTEMPTS
    # -----------------------------------------------------

    attempts = (
        QuizAttempt.objects
        .select_related(
            "assignment",
            "assignment__user",
            "assignment__training",
        )
        .order_by(
            "-completed_at",
            "-attempt_number",
        )
    )


    # Only the newest result for each employee
    # and training module should be analyzed.
    processed = set()


    for attempt in attempts:

        user = (
            attempt.assignment.user
        )

        training = (
            attempt.assignment.training
        )

        key = (
            user.user_id,
            training.training_id,
        )


        if key in processed:

            continue

        processed.add(
            key
        )


        percentage = Decimal(
            str(
                attempt.percentage
            )
        )


        priority = (
            get_priority_for_score(
                percentage
            )
        )


        # -------------------------------------------------
        # FIND CURRENT OPEN NEED
        # -------------------------------------------------

        open_need = (
            TrainingNeed.objects
            .filter(
                user=user,
                training=training,
                status=(
                    TrainingNeed
                    .Status
                    .OPEN
                ),
            )
            .order_by(
                "-identified_at"
            )
            .first()
        )


        # -------------------------------------------------
        # GOOD RESULT
        # -------------------------------------------------

        if priority is None:

            if open_need:

                open_need.status = (
                    TrainingNeed
                    .Status
                    .ADDRESSED
                )

                open_need.score = (
                    percentage
                )

                open_need.save(
                    update_fields=[
                        "status",
                        "score",
                    ]
                )

                addressed_count += 1

            continue


        # -------------------------------------------------
        # LOW RESULT
        # -------------------------------------------------

        if open_need:

            open_need.score = (
                percentage
            )

            open_need.priority = (
                priority
            )

            open_need.save(
                update_fields=[
                    "score",
                    "priority",
                ]
            )

            updated_count += 1

            continue


        # -------------------------------------------------
        # PREVENT OLD RESULTS RECREATING AN ADDRESSED NEED
        # -------------------------------------------------

        previous_need = (
            TrainingNeed.objects
            .filter(
                user=user,
                training=training,
            )
            .order_by(
                "-identified_at"
            )
            .first()
        )

        if (
            previous_need
            and
            previous_need.status
            ==
            TrainingNeed.Status.ADDRESSED
            and
            attempt.completed_at
            <= previous_need.identified_at
        ):

            continue


        # -------------------------------------------------
        # CREATE NEW NEED
        # -------------------------------------------------

        TrainingNeed.objects.create(
            user=user,
            training=training,
            score=percentage,
            priority=priority,
            status=(
                TrainingNeed
                .Status
                .OPEN
            ),
        )

        created_count += 1


    return {
        "created": created_count,
        "updated": updated_count,
        "addressed": addressed_count,
    }