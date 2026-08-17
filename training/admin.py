from django.contrib import admin

from .models import (
    EmployeeTraining,
    QuizAttempt,
    QuizQuestion,
    TrainingModule,
)
# =========================================================
# TRAINING MODULE ADMIN
# =========================================================

@admin.register(TrainingModule)
class TrainingModuleAdmin(
    admin.ModelAdmin
):

    list_display = [
        "training_id",
        "title",
        "topic",
        "status",
        "created_by",
        "created_at",
    ]

    list_filter = [
        "status",
        "topic",
    ]

    search_fields = [
        "title",
        "topic",
        "description",
    ]

    ordering = [
        "title"
    ]

    readonly_fields = [
        "training_id",
        "title",
        "topic",
        "description",
        "content",
        "status",
        "created_by",
        "created_at",
    ]

    def has_add_permission(
        self,
        request,
    ):
        return False

    def has_change_permission(
        self,
        request,
        obj=None,
    ):
        return False

    def has_delete_permission(
        self,
        request,
        obj=None,
    ):
        return False


# =========================================================
# EMPLOYEE TRAINING ADMIN
# =========================================================

@admin.register(EmployeeTraining)
class EmployeeTrainingAdmin(
    admin.ModelAdmin
):

    list_display = [
        "employee_training_id",
        "user",
        "training",
        "status",
        "progress_percent",
        "due_date",
        "assigned_by",
        "completed_at",
    ]

    list_filter = [
        "status",
        "training",
    ]

    search_fields = [
        "user__staff_no",
        "user__full_name",
        "user__email",
        "training__title",
    ]

    readonly_fields = [
        "employee_training_id",
        "user",
        "training",
        "assigned_by",
        "assigned_at",
        "due_date",
        "status",
        "progress_percent",
        "score",
        "passed",
        "completed_at",
    ]

    def has_add_permission(
        self,
        request,
    ):
        return False

    def has_change_permission(
        self,
        request,
        obj=None,
    ):
        return False

    def has_delete_permission(
        self,
        request,
        obj=None,
    ):
        return False

# =========================================================
# QUIZ QUESTION ADMIN
# =========================================================

@admin.register(QuizQuestion)
class QuizQuestionAdmin(
    admin.ModelAdmin
):

    list_display = [
        "question_id",
        "training",
        "question_text",
        "correct_option",
        "marks",
    ]

    list_filter = [
        "training",
    ]

    search_fields = [
        "question_text",
        "training__title",
    ]

    readonly_fields = [
        "training",
        "question_text",
        "option_a",
        "option_b",
        "option_c",
        "option_d",
        "correct_option",
        "marks",
    ]

    def has_add_permission(
        self,
        request,
    ):
        return False

    def has_change_permission(
        self,
        request,
        obj=None,
    ):
        return False

    def has_delete_permission(
        self,
        request,
        obj=None,
    ):
        return False


# =========================================================
# QUIZ ATTEMPT ADMIN
# =========================================================

@admin.register(QuizAttempt)
class QuizAttemptAdmin(
    admin.ModelAdmin
):

    list_display = [
        "attempt_id",
        "assignment",
        "attempt_number",
        "score",
        "percentage",
        "passed",
        "started_at",
        "completed_at",
    ]

    list_filter = [
        "passed",
        "completed_at",
    ]

    search_fields = [
        "assignment__user__staff_no",
        "assignment__user__full_name",
        "assignment__training__title",
    ]

    readonly_fields = [
        "assignment",
        "attempt_number",
        "score",
        "percentage",
        "passed",
        "started_at",
        "completed_at",
    ]

    def has_add_permission(
        self,
        request,
    ):
        return False

    def has_change_permission(
        self,
        request,
        obj=None,
    ):
        return False

    def has_delete_permission(
        self,
        request,
        obj=None,
    ):
        return False