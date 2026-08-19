from django.urls import path

from . import views


app_name = "reports"


urlpatterns = [

    path(
        "administrator/reports/",
        views.report_center,
        name="index",
    ),

    path(
        (
            "administrator/reports/"
            "compliance.csv"
        ),
        views.compliance_csv,
        name="compliance_csv",
    ),

    path(
        (
            "administrator/reports/"
            "training.csv"
        ),
        views.training_csv,
        name="training_csv",
    ),

    path(
        (
            "administrator/reports/"
            "pos-security.csv"
        ),
        views.pos_csv,
        name="pos_csv",
    ),

    path(
        (
            "administrator/reports/"
            "incidents.csv"
        ),
        views.incident_csv,
        name="incident_csv",
    ),
]