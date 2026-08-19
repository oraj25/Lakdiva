from django.urls import path

from . import views


urlpatterns = [
    path(
        "",
        views.home_redirect,
        name="home",
    ),

    path(
        "login/",
        views.login_view,
        name="login",
    ),

    path(
        "logout/",
        views.logout_view,
        name="logout",
    ),

    path(
        "employee/dashboard/",
        views.employee_dashboard,
        name="employee_dashboard",
    ),

    path(
        "administrator/dashboard/",
        views.administrator_dashboard,
        name="administrator_dashboard",
    ),

    # =====================================================
    # ADMINISTRATOR USER MANAGEMENT
    # =====================================================

    path(
        "administrator/users/",
        views.admin_user_list,
        name="admin_user_list",
    ),

    path(
        "administrator/users/create/",
        views.admin_user_create,
        name="admin_user_create",
    ),

    path(
        "administrator/users/<int:user_id>/",
        views.admin_user_detail,
        name="admin_user_detail",
    ),

    path(
        "administrator/users/<int:user_id>/edit/",
        views.admin_user_edit,
        name="admin_user_edit",
    ),

    path(
        "administrator/users/<int:user_id>/toggle/",
        views.admin_toggle_user,
        name="admin_toggle_user",
    ),

    path(
        "administrator/users/<int:user_id>/password/",
        views.admin_reset_password,
        name="admin_reset_password",
    ),
]