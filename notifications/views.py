from django.contrib import messages

from django.contrib.auth.decorators import (
    login_required,
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

from accounts.decorators import (
    role_required,
)

from accounts.models import (
    Role,
)

from .models import (
    Notification,
)

from .utils import (
    sync_employee_reminders,
)


# =========================================================
# HELPER - REDIRECT BASED ON USER ROLE
# =========================================================

def notification_home_name(
    user,
):

    if (
        user.role
        and
        user.role.role_name
        == Role.ADMIN
    ):

        return (
            "notifications:admin_list"
        )

    return (
        "notifications:employee_list"
    )


# =========================================================
# HELPER - FILTER NOTIFICATIONS
# =========================================================

def get_filtered_notifications(
    request,
):

    notifications = (
        Notification.objects
        .filter(
            user=request.user
        )
    )

    status = (
        request.GET
        .get(
            "status",
            "",
        )
        .strip()
    )

    notification_type = (
        request.GET
        .get(
            "type",
            "",
        )
        .strip()
    )


    if status == "unread":

        notifications = (
            notifications.filter(
                is_read=False
            )
        )


    elif status == "read":

        notifications = (
            notifications.filter(
                is_read=True
            )
        )


    if notification_type:

        notifications = (
            notifications.filter(
                notification_type=(
                    notification_type
                )
            )
        )


    return (
        notifications,
        status,
        notification_type,
    )


# =========================================================
# EMPLOYEE - NOTIFICATIONS
# =========================================================

@role_required(Role.EMPLOYEE)
def employee_notification_list(
    request,
):

    # Create any daily reminders
    # that are currently applicable.
    sync_employee_reminders(
        request.user
    )


    (
        notifications,
        selected_status,
        selected_type,
    ) = get_filtered_notifications(
        request
    )


    return render(
        request,
        "notifications/list.html",
        {
            "notifications": (
                notifications
            ),

            "selected_status": (
                selected_status
            ),

            "selected_type": (
                selected_type
            ),

            "notification_types": (
                Notification
                .NotificationType
                .choices
            ),

            "page_title": (
                "My Notifications"
            ),

            "page_description": (
                "Security policy, training "
                "and compliance notifications."
            ),

            "base_template": (
                "employee/base_employee.html"
            ),
        },
    )


# =========================================================
# ADMIN - NOTIFICATIONS
# =========================================================

@role_required(Role.ADMIN)
def admin_notification_list(
    request,
):

    (
        notifications,
        selected_status,
        selected_type,
    ) = get_filtered_notifications(
        request
    )


    return render(
        request,
        "notifications/list.html",
        {
            "notifications": (
                notifications
            ),

            "selected_status": (
                selected_status
            ),

            "selected_type": (
                selected_type
            ),

            "notification_types": (
                Notification
                .NotificationType
                .choices
            ),

            "page_title": (
                "Administrator Notifications"
            ),

            "page_description": (
                "Incident, risk and security "
                "management notifications."
            ),

            "base_template": (
                "administrator/"
                "base_admin.html"
            ),
        },
    )


# =========================================================
# MARK ONE AS READ
# =========================================================

@login_required
@require_POST
def mark_notification_read(
    request,
    notification_id,
):

    notification = get_object_or_404(

        Notification,

        notification_id=(
            notification_id
        ),

        user=request.user,
    )


    if not notification.is_read:

        notification.is_read = True

        notification.read_at = (
            timezone.now()
        )

        notification.save(
            update_fields=[
                "is_read",
                "read_at",
            ]
        )


    return redirect(
        notification_home_name(
            request.user
        )
    )


# =========================================================
# MARK ALL AS READ
# =========================================================

@login_required
@require_POST
def mark_all_notifications_read(
    request,
):

    Notification.objects.filter(
        user=request.user,
        is_read=False,
    ).update(
        is_read=True,
        read_at=timezone.now(),
    )


    messages.success(
        request,
        (
            "All notifications have "
            "been marked as read."
        ),
    )


    return redirect(
        notification_home_name(
            request.user
        )
    )