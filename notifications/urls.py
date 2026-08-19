from django.urls import path

from . import views


app_name = "notifications"


urlpatterns = [

    # =====================================================
    # EMPLOYEE
    # =====================================================

    path(
        "employee/notifications/",
        views.employee_notification_list,
        name="employee_list",
    ),


    # =====================================================
    # ADMINISTRATOR
    # =====================================================

    path(
        "administrator/notifications/",
        views.admin_notification_list,
        name="admin_list",
    ),


    # =====================================================
    # SHARED ACTIONS
    # =====================================================

    path(
        (
            "notifications/"
            "<int:notification_id>/read/"
        ),
        views.mark_notification_read,
        name="mark_read",
    ),

    path(
        "notifications/read-all/",
        views.mark_all_notifications_read,
        name="mark_all_read",
    ),
]