from django.urls import path

from . import views


app_name = "training"


urlpatterns = [

    # =====================================================
    # ADMINISTRATOR - TRAINING
    # =====================================================

    path(
        "administrator/training/",
        views.admin_training_list,
        name="admin_list",
    ),

    path(
        "administrator/training/create/",
        views.admin_training_create,
        name="admin_create",
    ),

    path(
        (
            "administrator/training/"
            "<int:training_id>/"
        ),
        views.admin_training_detail,
        name="admin_detail",
    ),

    path(
        (
            "administrator/training/"
            "<int:training_id>/edit/"
        ),
        views.admin_training_edit,
        name="admin_edit",
    ),

    path(
        (
            "administrator/training/"
            "<int:training_id>/publish/"
        ),
        views.admin_training_publish,
        name="admin_publish",
    ),

    path(
        (
            "administrator/training/"
            "<int:training_id>/archive/"
        ),
        views.admin_training_archive,
        name="admin_archive",
    ),

    path(
        (
            "administrator/training/"
            "<int:training_id>/assign/"
        ),
        views.admin_training_assign,
        name="admin_assign",
    ),


    # =====================================================
    # ADMINISTRATOR - QUIZ
    # =====================================================

    path(
        (
            "administrator/training/"
            "<int:training_id>/quiz/"
        ),
        views.admin_quiz_questions,
        name="admin_quiz_questions",
    ),

    path(
        (
            "administrator/training/"
            "<int:training_id>/quiz/add/"
        ),
        views.admin_quiz_question_create,
        name="admin_quiz_question_create",
    ),

    path(
        (
            "administrator/quiz/question/"
            "<int:question_id>/edit/"
        ),
        views.admin_quiz_question_edit,
        name="admin_quiz_question_edit",
    ),

    path(
        (
            "administrator/quiz/question/"
            "<int:question_id>/delete/"
        ),
        views.admin_quiz_question_delete,
        name="admin_quiz_question_delete",
    ),

    path(
        (
            "administrator/training/"
            "<int:training_id>/quiz/results/"
        ),
        views.admin_quiz_results,
        name="admin_quiz_results",
    ),


    # =====================================================
    # EMPLOYEE - TRAINING
    # =====================================================

    path(
        "employee/training/",
        views.employee_training_list,
        name="employee_list",
    ),

    path(
        (
            "employee/training/"
            "<int:assignment_id>/"
        ),
        views.employee_training_detail,
        name="employee_detail",
    ),

    path(
        (
            "employee/training/"
            "<int:assignment_id>/start/"
        ),
        views.employee_training_start,
        name="employee_start",
    ),

    path(
        (
            "employee/training/"
            "<int:assignment_id>/complete/"
        ),
        views.employee_training_complete,
        name="employee_complete",
    ),


    # =====================================================
    # EMPLOYEE - QUIZ
    # =====================================================

    path(
        (
            "employee/training/"
            "<int:assignment_id>/quiz/"
        ),
        views.employee_quiz_take,
        name="employee_quiz_take",
    ),

    path(
        (
            "employee/quiz/result/"
            "<int:attempt_id>/"
        ),
        views.employee_quiz_result,
        name="employee_quiz_result",
    ),
]