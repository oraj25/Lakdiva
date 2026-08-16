from django.urls import path

from . import views


urlpatterns = [

    # -------------------------------------
    # Home
    # -------------------------------------

    path(
        "",
        views.home_redirect,
        name="home",
    ),

    # -------------------------------------
    # Authentication
    # -------------------------------------

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

    # -------------------------------------
    # Employee
    # -------------------------------------

    path(
        "employee/dashboard/",
        views.employee_dashboard,
        name="employee_dashboard",
    ),

    # -------------------------------------
    # Administrator
    # -------------------------------------

    path(
        "administrator/dashboard/",
        views.administrator_dashboard,
        name="administrator_dashboard",
    ),
]