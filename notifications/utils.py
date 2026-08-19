from django.utils import timezone

from accounts.models import (
    Role,
    User,
)

from .models import (
    Notification,
)


# =========================================================
# CREATE ONE NOTIFICATION
# =========================================================

def create_notification(
    user,
    title,
    message,
    notification_type,
):

    return Notification.objects.create(
        user=user,
        title=title,
        message=message,
        notification_type=(
            notification_type
        ),
    )


# =========================================================
# NOTIFY ACTIVE ADMINISTRATORS
# =========================================================

def notify_active_admins(
    title,
    message,
    notification_type,
):

    administrators = (
        User.objects.filter(
            role__role_name=(
                Role.ADMIN
            ),
            status=(
                User.Status.ACTIVE
            ),
        )
    )

    notifications = [

        Notification(
            user=admin,
            title=title,
            message=message,
            notification_type=(
                notification_type
            ),
        )

        for admin in administrators
    ]

    if notifications:

        Notification.objects.bulk_create(
            notifications
        )

    return len(
        notifications
    )


# =========================================================
# NOTIFY ACTIVE EMPLOYEES
# =========================================================

def notify_active_employees(
    title,
    message,
    notification_type,
):

    employees = (
        User.objects.filter(
            role__role_name=(
                Role.EMPLOYEE
            ),
            status=(
                User.Status.ACTIVE
            ),
        )
    )

    notifications = [

        Notification(
            user=employee,
            title=title,
            message=message,
            notification_type=(
                notification_type
            ),
        )

        for employee in employees
    ]

    if notifications:

        Notification.objects.bulk_create(
            notifications
        )

    return len(
        notifications
    )


# =========================================================
# CREATE DAILY REMINDER ONLY ONCE
# =========================================================

def create_daily_notification_once(
    user,
    title,
    message,
    notification_type,
):

    today = timezone.localdate()

    already_created = (
        Notification.objects
        .filter(
            user=user,
            title=title,
            notification_type=(
                notification_type
            ),
            created_at__date=today,
        )
        .exists()
    )

    if already_created:

        return None

    return create_notification(
        user=user,
        title=title,
        message=message,
        notification_type=(
            notification_type
        ),
    )


# =========================================================
# EMPLOYEE REMINDER SYNCHRONIZATION
# =========================================================

def sync_employee_reminders(
    user,
):

    if (
        not user.is_authenticated
        or not user.role
        or user.role.role_name
        != Role.EMPLOYEE
    ):

        return


    # -----------------------------------------------------
    # POLICY REMINDER
    # -----------------------------------------------------

    from policies.models import (
        EMPLOYEE_POLICY_TYPES,
        Policy,
        PolicyAcknowledgement,
    )

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

    acknowledged_policy_ids = (
        PolicyAcknowledgement.objects
        .filter(
            user=user,
            policy__in=(
                published_policies
            ),
        )
        .values_list(
            "policy_id",
            flat=True,
        )
    )

    pending_policy_count = (
        published_policies
        .exclude(
            policy_id__in=(
                acknowledged_policy_ids
            )
        )
        .count()
    )

    if pending_policy_count > 0:

        create_daily_notification_once(

            user=user,

            title=(
                "Policy Acknowledgement Required"
            ),

            message=(
                f"You have "
                f"{pending_policy_count} "
                f"published security "
                f"polic"
                f"{'y' if pending_policy_count == 1 else 'ies'} "
                f"waiting for acknowledgement."
            ),

            notification_type=(
                Notification
                .NotificationType
                .POLICY
            ),
        )


    # -----------------------------------------------------
    # TRAINING REMINDER
    # -----------------------------------------------------

    from training.models import (
        EmployeeTraining,
    )

    pending_training_count = (
        EmployeeTraining.objects
        .filter(
            user=user
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

    if pending_training_count > 0:

        create_daily_notification_once(

            user=user,

            title=(
                "Security Training Pending"
            ),

            message=(
                f"You have "
                f"{pending_training_count} "
                f"security training "
                f"assignment"
                f"{'' if pending_training_count == 1 else 's'} "
                f"to complete."
            ),

            notification_type=(
                Notification
                .NotificationType
                .TRAINING
            ),
        )