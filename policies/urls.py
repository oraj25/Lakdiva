from django.urls import path

from . import views


app_name = "policies"


urlpatterns = [

    # =====================================================
    # ADMIN
    # =====================================================

    path(
        "administrator/policies/",
        views.admin_policy_list,
        name="admin_list",
    ),

    path(
        "administrator/policies/create/",
        views.admin_policy_create,
        name="admin_create",
    ),

    path(
        (
            "administrator/policies/"
            "<int:policy_id>/"
        ),
        views.admin_policy_detail,
        name="admin_detail",
    ),

    path(
        (
            "administrator/policies/"
            "<int:policy_id>/edit/"
        ),
        views.admin_policy_edit,
        name="admin_edit",
    ),

    path(
        (
            "administrator/policies/"
            "<int:policy_id>/publish/"
        ),
        views.admin_policy_publish,
        name="admin_publish",
    ),

    path(
        (
            "administrator/policies/"
            "<int:policy_id>/archive/"
        ),
        views.admin_policy_archive,
        name="admin_archive",
    ),

    path(
        (
            "administrator/policies/"
            "<int:policy_id>/new-version/"
        ),
        views.admin_policy_new_version,
        name="admin_new_version",
    ),


    # =====================================================
    # EMPLOYEE
    # =====================================================

    path(
        "employee/policies/",
        views.employee_policy_list,
        name="employee_list",
    ),

    path(
        (
            "employee/policies/"
            "<int:policy_id>/"
        ),
        views.employee_policy_detail,
        name="employee_detail",
    ),

    path(
        (
            "employee/policies/"
            "<int:policy_id>/acknowledge/"
        ),
        views.employee_policy_acknowledge,
        name="employee_acknowledge",
    ),
]