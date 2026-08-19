from django.urls import path

from . import views


app_name = "compliance"


urlpatterns = [

    path(
        "my/",
        views.my_compliance,
        name="my_compliance",
    ),

    path(
        "administrator/",
        views.admin_compliance,
        name="admin_compliance",
    ),

    path(
        "administrator/employee/<int:user_id>/",
        views.admin_employee_compliance,
        name="admin_employee_compliance",
    ),

]