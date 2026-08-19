from django.urls import path

from . import views


app_name = "training_needs"


urlpatterns = [

    path(
        "administrator/training-needs/",
        views.admin_training_need_list,
        name="admin_list",
    ),

    path(
        (
            "administrator/"
            "training-needs/analyze/"
        ),
        views.admin_analyze_training_needs,
        name="admin_analyze",
    ),

    path(
        (
            "administrator/"
            "training-needs/"
            "<int:need_id>/assign/"
        ),
        views.admin_assign_training,
        name="admin_assign",
    ),
]