from django.urls import path

from . import views


app_name = "auditlog"


urlpatterns = [

    path(
        "administrator/audit-logs/",
        views.admin_audit_log_list,
        name="admin_list",
    ),

    path(
        (
            "administrator/"
            "audit-logs/"
            "<int:log_id>/"
        ),
        views.admin_audit_log_detail,
        name="admin_detail",
    ),
]