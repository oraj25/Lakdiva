from django.urls import path

from . import views


app_name = "incidents"


urlpatterns = [

    # =====================================================
    # EMPLOYEE
    # =====================================================

    path(
        "employee/incidents/",
        views.employee_incident_list,
        name="employee_list",
    ),

    path(
        "employee/incidents/report/",
        views.employee_incident_create,
        name="employee_create",
    ),

    path(
        (
            "employee/incidents/"
            "<int:incident_id>/"
        ),
        views.employee_incident_detail,
        name="employee_detail",
    ),


    # =====================================================
    # SECURE EVIDENCE
    # =====================================================

    path(
        (
            "incident-evidence/"
            "<int:evidence_id>/download/"
        ),
        views.evidence_download,
        name="evidence_download",
    ),


    # =====================================================
    # ADMINISTRATOR
    # =====================================================

    path(
        "administrator/incidents/",
        views.admin_incident_list,
        name="admin_list",
    ),

    path(
        (
            "administrator/incidents/"
            "<int:incident_id>/"
        ),
        views.admin_incident_detail,
        name="admin_detail",
    ),
    path(
    (
        "administrator/incidents/"
        "<int:incident_id>/risk-assessment/"
    ),
    views.admin_risk_assessment_create,
    name="admin_risk_assessment",
    ),

    path(
    (
        "administrator/incidents/"
        "<int:incident_id>/action/"
    ),
    views.admin_incident_action,
    name="admin_action",
    ),
]