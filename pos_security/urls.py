from django.urls import path

from . import views


app_name = "pos_security"


urlpatterns = [

    # =====================================================
    # EMPLOYEE
    # =====================================================

    path(
        "employee/pos/",
        views.employee_pos_list,
        name="employee_list",
    ),

    path(
        "employee/pos/start/",
        views.employee_shift_start,
        name="employee_shift_start",
    ),

    path(
        "employee/pos/<int:shift_id>/",
        views.employee_shift_detail,
        name="employee_detail",
    ),

    path(
        (
            "employee/pos/"
            "<int:shift_id>/cash/"
        ),
        views.employee_cash_update,
        name="employee_cash_update",
    ),

    path(
        (
            "employee/pos/"
            "<int:shift_id>/security-check/"
        ),
        views.employee_security_check,
        name="employee_security_check",
    ),

    path(
        (
            "employee/pos/"
            "<int:shift_id>/close/"
        ),
        views.employee_shift_close,
        name="employee_shift_close",
    ),


    # =====================================================
    # ADMINISTRATOR
    # =====================================================

    path(
        "administrator/pos/",
        views.admin_pos_list,
        name="admin_list",
    ),

    path(
        (
            "administrator/pos/"
            "<int:shift_id>/"
        ),
        views.admin_pos_detail,
        name="admin_detail",
    ),
]