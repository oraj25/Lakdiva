from accounts.models import (
    Role,
    User,
)

from .models import Notification


def notify_active_admins(
    title,
    message,
    notification_type,
):
    """
    Create an in-app notification
    for every active Administrator.
    """

    administrators = (
        User.objects.filter(
            role__role_name=Role.ADMIN,
            status=User.Status.ACTIVE,
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

    return len(notifications)