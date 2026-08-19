from .models import (
    Notification,
)


# =========================================================
# GLOBAL NOTIFICATION COUNT
# =========================================================

def notification_context(
    request,
):

    if not request.user.is_authenticated:

        return {
            "global_unread_notification_count": 0
        }


    unread_count = (
        Notification.objects
        .filter(
            user=request.user,
            is_read=False,
        )
        .count()
    )


    return {
        "global_unread_notification_count": (
            unread_count
        )
    }