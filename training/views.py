from django.contrib import messages

from django.db import transaction

from django.db.models import (
    Avg,
    Max,
    Q,
    Sum,
)

from django.shortcuts import (
    get_object_or_404,
    redirect,
    render,
)

from django.utils.dateparse import (
    parse_datetime,
)

from django.utils import timezone

from django.views.decorators.http import (
    require_POST,
)

from accounts.decorators import (
    role_required,
)

from accounts.models import (
    Role,
    User,
)

from auditlog.utils import (
    log_action,
)

from notifications.models import (
    Notification,
)

from notifications.utils import (
    create_notification,
)

from .models import (
    EmployeeTraining,
    QuizAttempt,
    QuizQuestion,
    TrainingModule,
)

from .forms import (
    QuizQuestionForm,
    TrainingAssignmentForm,
    TrainingModuleForm,
)

import uuid

from decimal import (
    Decimal,
    ROUND_HALF_UP,
)

from django.conf import settings
# =========================================================
# ADMIN - TRAINING LIST
# =========================================================

@role_required(Role.ADMIN)
def admin_training_list(request):

    training_modules = (
        TrainingModule.objects
        .select_related(
            "created_by"
        )
        .all()
    )

    search = (
        request.GET
        .get(
            "search",
            "",
        )
        .strip()
    )

    status = (
        request.GET
        .get(
            "status",
            "",
        )
        .strip()
    )

    topic = (
        request.GET
        .get(
            "topic",
            "",
        )
        .strip()
    )

    if search:

        training_modules = (
            training_modules.filter(
                Q(
                    title__icontains=search
                )
                |
                Q(
                    description__icontains=search
                )
                |
                Q(
                    topic__icontains=search
                )
            )
        )

    if status:

        training_modules = (
            training_modules.filter(
                status=status
            )
        )

    if topic:

        training_modules = (
            training_modules.filter(
                topic=topic
            )
        )

    return render(
        request,
        "administrator/training/list.html",
        {
            "training_modules": (
                training_modules
            ),

            "search": search,

            "selected_status": status,

            "selected_topic": topic,

            "statuses": (
                TrainingModule.Status.choices
            ),

            "topics": (
                TrainingModule.Topic.choices
            ),
        },
    )


# =========================================================
# ADMIN - CREATE
# =========================================================

@role_required(Role.ADMIN)
def admin_training_create(request):

    form = TrainingModuleForm(
        request.POST or None
    )

    if (
        request.method == "POST"
        and form.is_valid()
    ):

        training = form.save(
            commit=False
        )

        training.created_by = (
            request.user
        )

        training.status = (
            TrainingModule.Status.DRAFT
        )

        training.save()

        log_action(
            request=request,
            action="TRAINING_CREATED",
            entity_type="Training",
            entity_id=(
                training.training_id
            ),
            details=(
                f"Created training "
                f"'{training.title}' as Draft."
            ),
        )

        messages.success(
            request,
            (
                "Training module created "
                "successfully as Draft."
            ),
        )

        return redirect(
            "training:admin_detail",
            training_id=(
                training.training_id
            ),
        )

    return render(
        request,
        "administrator/training/form.html",
        {
            "form": form,
            "page_title": (
                "Create Security Training"
            ),
            "button_text": (
                "Create Draft"
            ),
        },
    )


# =========================================================
# ADMIN - DETAIL
# =========================================================

@role_required(Role.ADMIN)
def admin_training_detail(
    request,
    training_id,
):

    training = get_object_or_404(
        TrainingModule.objects
        .select_related(
            "created_by"
        ),
        training_id=training_id,
    )

    assignments = (
        EmployeeTraining.objects
        .filter(
            training=training
        )
        .select_related(
            "user"
        )
    )

    total_assigned = (
        assignments.count()
    )

    assigned_count = (
        assignments.filter(
            status=(
                EmployeeTraining
                .Status
                .ASSIGNED
            )
        ).count()
    )

    in_progress_count = (
        assignments.filter(
            status=(
                EmployeeTraining
                .Status
                .IN_PROGRESS
            )
        ).count()
    )

    completed_count = (
        assignments.filter(
            status=(
                EmployeeTraining
                .Status
                .COMPLETED
            )
        ).count()
    )

    return render(
        request,
        (
            "administrator/"
            "training/detail.html"
        ),
        {
            "training": training,

            "assignments": assignments,

            "total_assigned": (
                total_assigned
            ),

            "assigned_count": (
                assigned_count
            ),

            "in_progress_count": (
                in_progress_count
            ),

            "completed_count": (
                completed_count
            ),
        },
    )


# =========================================================
# ADMIN - EDIT DRAFT
# =========================================================

@role_required(Role.ADMIN)
def admin_training_edit(
    request,
    training_id,
):

    training = get_object_or_404(
        TrainingModule,
        training_id=training_id,
    )

    if (
        training.status
        != TrainingModule.Status.DRAFT
    ):

        messages.error(
            request,
            (
                "Only Draft training modules "
                "can be edited."
            ),
        )

        return redirect(
            "training:admin_detail",
            training_id=(
                training.training_id
            ),
        )

    form = TrainingModuleForm(
        request.POST or None,
        instance=training,
    )

    if (
        request.method == "POST"
        and form.is_valid()
    ):

        training = form.save()

        log_action(
            request=request,
            action="TRAINING_UPDATED",
            entity_type="Training",
            entity_id=(
                training.training_id
            ),
            details=(
                f"Updated Draft training "
                f"'{training.title}'."
            ),
        )

        messages.success(
            request,
            "Training Draft updated.",
        )

        return redirect(
            "training:admin_detail",
            training_id=(
                training.training_id
            ),
        )

    return render(
        request,
        "administrator/training/form.html",
        {
            "form": form,
            "training": training,
            "page_title": (
                "Edit Security Training"
            ),
            "button_text": (
                "Save Changes"
            ),
        },
    )


# =========================================================
# ADMIN - PUBLISH
# =========================================================

@role_required(Role.ADMIN)
@require_POST
def admin_training_publish(
    request,
    training_id,
):

    training = get_object_or_404(
        TrainingModule,
        training_id=training_id,
    )

    if (
        training.status
        != TrainingModule.Status.DRAFT
    ):

        messages.error(
            request,
            (
                "Only Draft training "
                "can be published."
            ),
        )

        return redirect(
            "training:admin_detail",
            training_id=(
                training.training_id
            ),
        )

    training.status = (
        TrainingModule.Status.PUBLISHED
    )

    training.save(
        update_fields=[
            "status"
        ]
    )

    log_action(
        request=request,
        action="TRAINING_PUBLISHED",
        entity_type="Training",
        entity_id=training.training_id,
        details=(
            f"Published training "
            f"'{training.title}'."
        ),
    )

    messages.success(
        request,
        (
            "Training module published "
            "successfully."
        ),
    )

    return redirect(
        "training:admin_detail",
        training_id=(
            training.training_id
        ),
    )


# =========================================================
# ADMIN - ARCHIVE
# =========================================================

@role_required(Role.ADMIN)
@require_POST
def admin_training_archive(
    request,
    training_id,
):

    training = get_object_or_404(
        TrainingModule,
        training_id=training_id,
    )

    if (
        training.status
        != TrainingModule.Status.PUBLISHED
    ):

        messages.error(
            request,
            (
                "Only Published training "
                "can be archived."
            ),
        )

        return redirect(
            "training:admin_detail",
            training_id=(
                training.training_id
            ),
        )

    training.status = (
        TrainingModule.Status.ARCHIVED
    )

    training.save(
        update_fields=[
            "status"
        ]
    )

    log_action(
        request=request,
        action="TRAINING_ARCHIVED",
        entity_type="Training",
        entity_id=training.training_id,
        details=(
            f"Archived training "
            f"'{training.title}'."
        ),
    )

    messages.success(
        request,
        "Training module archived.",
    )

    return redirect(
        "training:admin_detail",
        training_id=(
            training.training_id
        ),
    )


# =========================================================
# ADMIN - ASSIGN TRAINING
# =========================================================

@role_required(Role.ADMIN)
def admin_training_assign(
    request,
    training_id,
):

    training = get_object_or_404(
        TrainingModule,
        training_id=training_id,
    )

    if (
        training.status
        != TrainingModule.Status.PUBLISHED
    ):

        messages.error(
            request,
            (
                "Only Published training "
                "can be assigned."
            ),
        )

        return redirect(
            "training:admin_detail",
            training_id=(
                training.training_id
            ),
        )

    form = TrainingAssignmentForm(
        request.POST or None
    )

    if (
        request.method == "POST"
        and form.is_valid()
    ):

        assign_to_all = (
            form.cleaned_data[
                "assign_to_all"
            ]
        )

        due_date = (
            form.cleaned_data[
                "due_date"
            ]
        )

        if assign_to_all:

            employees = (
                User.objects.filter(
                    role__role_name=(
                        Role.EMPLOYEE
                    ),
                    status=(
                        User.Status.ACTIVE
                    ),
                )
            )

        else:

            employees = (
                form.cleaned_data[
                    "employees"
                ]
            )

        created_count = 0
        skipped_count = 0

        with transaction.atomic():

            for employee in employees:

                # -------------------------------------------------
                # PREVENT DUPLICATE UNFINISHED ASSIGNMENT
                # -------------------------------------------------

                existing = (
                    EmployeeTraining
                    .objects
                    .filter(
                        user=employee,
                        training=training,
                    )
                    .exclude(
                        status=(
                            EmployeeTraining
                            .Status
                            .COMPLETED
                        )
                    )
                    .exists()
                )

                if existing:

                    skipped_count += 1

                    continue


                # -------------------------------------------------
                # CREATE TRAINING ASSIGNMENT
                # -------------------------------------------------

                assignment = (
                    EmployeeTraining
                    .objects
                    .create(
                        user=employee,
                        training=training,
                        assigned_by=(
                            request.user
                        ),
                        due_date=due_date,
                        status=(
                            EmployeeTraining
                            .Status
                            .ASSIGNED
                        ),
                        progress_percent=0,
                    )
                )


                # -------------------------------------------------
                # EMPLOYEE NOTIFICATION
                # -------------------------------------------------

                create_notification(
                    user=employee,

                    title=(
                        "New Security Training Assigned"
                    ),

                    message=(
                        f"'{training.title}' "
                        f"has been assigned to you."
                        +
                        (
                            f" Due date: "
                            f"{due_date}."
                            if due_date
                            else ""
                        )
                    ),

                    notification_type=(
                        Notification
                        .NotificationType
                        .TRAINING
                    ),
                )


                created_count += 1


                # -------------------------------------------------
                # AUDIT LOG
                # -------------------------------------------------

                log_action(
                    request=request,
                    action=(
                        "TRAINING_ASSIGNED"
                    ),
                    entity_type=(
                        "EmployeeTraining"
                    ),
                    entity_id=(
                        assignment
                        .employee_training_id
                    ),
                    details=(
                        f"Assigned "
                        f"'{training.title}' "
                        f"to employee "
                        f"{employee.staff_no}."
                    ),
                )


        # -----------------------------------------------------
        # SUCCESS MESSAGE
        # -----------------------------------------------------

        messages.success(
            request,
            (
                f"Training assigned to "
                f"{created_count} employee(s). "
                f"{skipped_count} existing "
                f"assignment(s) skipped."
            ),
        )

        return redirect(
            "training:admin_detail",
            training_id=(
                training.training_id
            ),
        )

    return render(
        request,
        (
            "administrator/"
            "training/assign.html"
        ),
        {
            "training": training,
            "form": form,
        },
    )

# =========================================================
# EMPLOYEE - TRAINING LIST
# =========================================================

@role_required(Role.EMPLOYEE)
def employee_training_list(
    request,
):

    assignments = (
        EmployeeTraining.objects
        .filter(
            user=request.user
        )
        .select_related(
            "training",
            "assigned_by",
        )
    )

    assigned_count = (
        assignments.filter(
            status=(
                EmployeeTraining
                .Status
                .ASSIGNED
            )
        ).count()
    )

    in_progress_count = (
        assignments.filter(
            status=(
                EmployeeTraining
                .Status
                .IN_PROGRESS
            )
        ).count()
    )

    completed_count = (
        assignments.filter(
            status=(
                EmployeeTraining
                .Status
                .COMPLETED
            )
        ).count()
    )

    return render(
        request,
        "employee/training/list.html",
        {
            "assignments": assignments,

            "assigned_count": (
                assigned_count
            ),

            "in_progress_count": (
                in_progress_count
            ),

            "completed_count": (
                completed_count
            ),
        },
    )


# =========================================================
# EMPLOYEE - TRAINING DETAIL
# =========================================================

@role_required(Role.EMPLOYEE)
def employee_training_detail(
    request,
    assignment_id,
):

    assignment = get_object_or_404(
        EmployeeTraining.objects
        .select_related(
            "training",
            "assigned_by",
        ),
        employee_training_id=(
            assignment_id
        ),
        user=request.user,
    )

    return render(
        request,
        (
            "employee/"
            "training/detail.html"
        ),
        {
            "assignment": assignment,
            "training": (
                assignment.training
            ),
        },
    )


# =========================================================
# EMPLOYEE - START TRAINING
# =========================================================

@role_required(Role.EMPLOYEE)
@require_POST
def employee_training_start(
    request,
    assignment_id,
):

    with transaction.atomic():

        assignment = get_object_or_404(
            EmployeeTraining.objects
            .select_for_update()
            .select_related(
                "training"
            ),
            employee_training_id=(
                assignment_id
            ),
            user=request.user,
        )

        if (
            assignment.status
            == EmployeeTraining
            .Status
            .COMPLETED
        ):

            messages.warning(
                request,
                (
                    "This training has "
                    "already been completed."
                ),
            )

        elif (
            assignment.status
            == EmployeeTraining
            .Status
            .ASSIGNED
        ):

            assignment.status = (
                EmployeeTraining
                .Status
                .IN_PROGRESS
            )

            assignment.save(
                update_fields=[
                    "status"
                ]
            )

            log_action(
                request=request,
                action="TRAINING_STARTED",
                entity_type=(
                    "EmployeeTraining"
                ),
                entity_id=(
                    assignment
                    .employee_training_id
                ),
                details=(
                    f"Employee "
                    f"{request.user.staff_no} "
                    f"started training "
                    f"'{assignment.training.title}'."
                ),
            )

            messages.success(
                request,
                "Training started.",
            )

    return redirect(
        "training:employee_detail",
        assignment_id=(
            assignment.employee_training_id
        ),
    )


# =========================================================
# EMPLOYEE - COMPLETE TRAINING
# =========================================================

@role_required(Role.EMPLOYEE)
@require_POST
def employee_training_complete(
    request,
    assignment_id,
):

    with transaction.atomic():

        assignment = get_object_or_404(
            EmployeeTraining.objects
            .select_for_update()
            .select_related(
                "training"
            ),
            employee_training_id=(
                assignment_id
            ),
            user=request.user,
        )

        if (
            assignment.status
            == EmployeeTraining
            .Status
            .ASSIGNED
        ):

            messages.error(
                request,
                (
                    "Start the training "
                    "before completing it."
                ),
            )

            return redirect(
                "training:employee_detail",
                assignment_id=(
                    assignment
                    .employee_training_id
                ),
            )

        if (
            assignment.status
            == EmployeeTraining
            .Status
            .COMPLETED
        ):

            messages.warning(
                request,
                (
                    "This training has "
                    "already been completed."
                ),
            )

            return redirect(
                "training:employee_detail",
                assignment_id=(
                    assignment
                    .employee_training_id
                ),
            )

        assignment.status = (
            EmployeeTraining
            .Status
            .COMPLETED
        )

        assignment.progress_percent = 100

        assignment.completed_at = (
            timezone.now()
        )

        assignment.save(
            update_fields=[
                "status",
                "progress_percent",
                "completed_at",
            ]
        )

        log_action(
            request=request,
            action="TRAINING_COMPLETED",
            entity_type=(
                "EmployeeTraining"
            ),
            entity_id=(
                assignment
                .employee_training_id
            ),
            details=(
                f"Employee "
                f"{request.user.staff_no} "
                f"completed training "
                f"'{assignment.training.title}'."
            ),
        )

        messages.success(
            request,
            (
                "Training completed "
                "successfully."
            ),
        )

    return redirect(
        "training:employee_detail",
        assignment_id=(
            assignment.employee_training_id
        ),
    )

# =========================================================
# QUIZ HELPERS
# =========================================================

def quiz_is_locked(training):
    """
    Once any employee has submitted a quiz attempt,
    quiz questions cannot be modified.

    This prevents previous quiz results from becoming
    inconsistent with changed questions.
    """

    return QuizAttempt.objects.filter(
        assignment__training=training
    ).exists()


def get_quiz_pass_percentage():
    """
    Read the configured pass percentage.
    """

    return Decimal(
        str(
            getattr(
                settings,
                "QUIZ_PASS_PERCENTAGE",
                60,
            )
        )
    )


# =========================================================
# ADMIN - QUIZ QUESTION LIST
# =========================================================

@role_required(Role.ADMIN)
def admin_quiz_questions(
    request,
    training_id,
):

    training = get_object_or_404(
        TrainingModule,
        training_id=training_id,
    )

    questions = (
        QuizQuestion.objects
        .filter(
            training=training
        )
        .order_by(
            "question_id"
        )
    )

    total_marks = (
        questions.aggregate(
            total=Sum("marks")
        )["total"]
        or 0
    )

    locked = quiz_is_locked(
        training
    )

    return render(
        request,
        (
            "administrator/"
            "quiz/questions.html"
        ),
        {
            "training": training,
            "questions": questions,
            "total_marks": total_marks,
            "locked": locked,
            "pass_percentage": (
                get_quiz_pass_percentage()
            ),
        },
    )


# =========================================================
# ADMIN - CREATE QUIZ QUESTION
# =========================================================

@role_required(Role.ADMIN)
def admin_quiz_question_create(
    request,
    training_id,
):

    training = get_object_or_404(
        TrainingModule,
        training_id=training_id,
    )

    if (
        training.status
        == TrainingModule.Status.ARCHIVED
    ):

        messages.error(
            request,
            (
                "Quiz questions cannot be added "
                "to archived training."
            ),
        )

        return redirect(
            "training:admin_quiz_questions",
            training_id=training.training_id,
        )

    if quiz_is_locked(training):

        messages.error(
            request,
            (
                "Quiz questions cannot be changed "
                "because employees have already "
                "submitted quiz attempts."
            ),
        )

        return redirect(
            "training:admin_quiz_questions",
            training_id=training.training_id,
        )

    form = QuizQuestionForm(
        request.POST or None
    )

    if (
        request.method == "POST"
        and form.is_valid()
    ):

        question = form.save(
            commit=False
        )

        question.training = training

        question.save()

        log_action(
            request=request,
            action="QUIZ_QUESTION_CREATED",
            entity_type="QuizQuestion",
            entity_id=(
                question.question_id
            ),
            details=(
                f"Created quiz question "
                f"for training "
                f"'{training.title}'."
            ),
        )

        messages.success(
            request,
            (
                "Quiz question created "
                "successfully."
            ),
        )

        return redirect(
            "training:admin_quiz_questions",
            training_id=training.training_id,
        )

    return render(
        request,
        (
            "administrator/"
            "quiz/question_form.html"
        ),
        {
            "training": training,
            "form": form,
            "page_title": (
                "Add Quiz Question"
            ),
            "button_text": (
                "Add Question"
            ),
        },
    )


# =========================================================
# ADMIN - EDIT QUIZ QUESTION
# =========================================================

@role_required(Role.ADMIN)
def admin_quiz_question_edit(
    request,
    question_id,
):

    question = get_object_or_404(
        QuizQuestion.objects
        .select_related(
            "training"
        ),
        question_id=question_id,
    )

    training = question.training

    if quiz_is_locked(training):

        messages.error(
            request,
            (
                "Quiz questions cannot be edited "
                "after quiz attempts exist."
            ),
        )

        return redirect(
            "training:admin_quiz_questions",
            training_id=training.training_id,
        )

    form = QuizQuestionForm(
        request.POST or None,
        instance=question,
    )

    if (
        request.method == "POST"
        and form.is_valid()
    ):

        question = form.save()

        log_action(
            request=request,
            action="QUIZ_QUESTION_UPDATED",
            entity_type="QuizQuestion",
            entity_id=(
                question.question_id
            ),
            details=(
                f"Updated quiz question "
                f"for training "
                f"'{training.title}'."
            ),
        )

        messages.success(
            request,
            (
                "Quiz question updated "
                "successfully."
            ),
        )

        return redirect(
            "training:admin_quiz_questions",
            training_id=training.training_id,
        )

    return render(
        request,
        (
            "administrator/"
            "quiz/question_form.html"
        ),
        {
            "training": training,
            "form": form,
            "page_title": (
                "Edit Quiz Question"
            ),
            "button_text": (
                "Save Changes"
            ),
        },
    )


# =========================================================
# ADMIN - DELETE QUESTION
# =========================================================

@role_required(Role.ADMIN)
@require_POST
def admin_quiz_question_delete(
    request,
    question_id,
):

    question = get_object_or_404(
        QuizQuestion.objects
        .select_related(
            "training"
        ),
        question_id=question_id,
    )

    training = question.training

    if quiz_is_locked(training):

        messages.error(
            request,
            (
                "Quiz questions cannot be deleted "
                "after quiz attempts exist."
            ),
        )

        return redirect(
            "training:admin_quiz_questions",
            training_id=training.training_id,
        )

    question_id_value = (
        question.question_id
    )

    question.delete()

    log_action(
        request=request,
        action="QUIZ_QUESTION_DELETED",
        entity_type="QuizQuestion",
        entity_id=question_id_value,
        details=(
            f"Deleted quiz question "
            f"from training "
            f"'{training.title}'."
        ),
    )

    messages.success(
        request,
        "Quiz question deleted.",
    )

    return redirect(
        "training:admin_quiz_questions",
        training_id=training.training_id,
    )


# =========================================================
# ADMIN - QUIZ RESULTS
# =========================================================

@role_required(Role.ADMIN)
def admin_quiz_results(
    request,
    training_id,
):

    training = get_object_or_404(
        TrainingModule,
        training_id=training_id,
    )

    attempts = (
        QuizAttempt.objects
        .filter(
            assignment__training=training
        )
        .select_related(
            "assignment",
            "assignment__user",
        )
        .order_by(
            "-completed_at"
        )
    )

    total_attempts = (
        attempts.count()
    )

    passed_count = (
        attempts.filter(
            passed=True
        ).count()
    )

    failed_count = (
        attempts.filter(
            passed=False
        ).count()
    )

    average_percentage = (
        attempts.aggregate(
            average=Avg(
                "percentage"
            )
        )["average"]
    )

    low_performance_employees = (
        attempts
        .filter(
            passed=False
        )
        .values(
            "assignment__user_id"
        )
        .distinct()
        .count()
    )

    return render(
        request,
        (
            "administrator/"
            "quiz/results.html"
        ),
        {
            "training": training,
            "attempts": attempts,

            "total_attempts": (
                total_attempts
            ),

            "passed_count": (
                passed_count
            ),

            "failed_count": (
                failed_count
            ),

            "average_percentage": (
                average_percentage
            ),

            "low_performance_employees": (
                low_performance_employees
            ),

            "pass_percentage": (
                get_quiz_pass_percentage()
            ),
        },
    )


# =========================================================
# EMPLOYEE - TAKE QUIZ
# =========================================================

@role_required(Role.EMPLOYEE)
def employee_quiz_take(
    request,
    assignment_id,
):

    assignment = get_object_or_404(
        EmployeeTraining.objects
        .select_related(
            "training"
        ),
        employee_training_id=(
            assignment_id
        ),
        user=request.user,
    )

    training = assignment.training

    # -----------------------------------------------------
    # Training must be completed first
    # -----------------------------------------------------

    if (
        assignment.status
        != EmployeeTraining
        .Status
        .COMPLETED
    ):

        messages.error(
            request,
            (
                "Complete the training module "
                "before taking the quiz."
            ),
        )

        return redirect(
            "training:employee_detail",
            assignment_id=(
                assignment
                .employee_training_id
            ),
        )

    questions = list(
        QuizQuestion.objects
        .filter(
            training=training
        )
        .order_by(
            "question_id"
        )
    )

    if not questions:

        messages.warning(
            request,
            (
                "A quiz has not yet been "
                "created for this training."
            ),
        )

        return redirect(
            "training:employee_detail",
            assignment_id=(
                assignment
                .employee_training_id
            ),
        )

    total_marks = sum(
        question.marks
        for question in questions
    )

    if total_marks <= 0:

        messages.error(
            request,
            (
                "This quiz has an invalid "
                "mark configuration."
            ),
        )

        return redirect(
            "training:employee_detail",
            assignment_id=(
                assignment
                .employee_training_id
            ),
        )

    # -----------------------------------------------------
    # Session data prevents accidental double submissions
    # and records when the quiz started.
    # -----------------------------------------------------

    start_key = (
        f"quiz_start_{assignment_id}"
    )

    token_key = (
        f"quiz_token_{assignment_id}"
    )

    if request.method == "GET":

        if not request.session.get(
            start_key
        ):

            request.session[
                start_key
            ] = (
                timezone.now()
                .isoformat()
            )

        if not request.session.get(
            token_key
        ):

            request.session[
                token_key
            ] = uuid.uuid4().hex


    # -----------------------------------------------------
    # SUBMIT QUIZ
    # -----------------------------------------------------

    if request.method == "POST":

        submitted_token = (
            request.POST.get(
                "quiz_token"
            )
        )

        session_token = (
            request.session.get(
                token_key
            )
        )

        if (
            not submitted_token
            or not session_token
            or submitted_token
            != session_token
        ):

            messages.error(
                request,
                (
                    "This quiz submission is "
                    "invalid or has already "
                    "been processed."
                ),
            )

            return redirect(
                "training:employee_detail",
                assignment_id=(
                    assignment
                    .employee_training_id
                ),
            )

        earned_marks = 0

        # -------------------------------------------------
        # Validate every answer
        # -------------------------------------------------

        for question in questions:

            answer = (
                request.POST.get(
                    f"question_"
                    f"{question.question_id}"
                )
            )

            valid_options = [
                "A",
                "B",
            ]

            if question.option_c:
                valid_options.append("C")

            if question.option_d:
                valid_options.append("D")

            if (
                not answer
                or answer
                not in valid_options
            ):

                messages.error(
                    request,
                    (
                        "Please answer every "
                        "quiz question."
                    ),
                )

                return render(
                    request,
                    (
                        "employee/"
                        "quiz/take.html"
                    ),
                    {
                        "assignment": (
                            assignment
                        ),
                        "training": (
                            training
                        ),
                        "questions": (
                            questions
                        ),
                        "total_marks": (
                            total_marks
                        ),
                        "quiz_token": (
                            session_token
                        ),
                        "pass_percentage": (
                            get_quiz_pass_percentage()
                        ),
                    },
                )

            if (
                answer
                == question.correct_option
            ):

                earned_marks += (
                    question.marks
                )

        # -------------------------------------------------
        # CALCULATE SCORE
        # -------------------------------------------------

        percentage = (
            (
                Decimal(
                    earned_marks
                )
                /
                Decimal(
                    total_marks
                )
            )
            *
            Decimal("100")
        ).quantize(
            Decimal("0.01"),
            rounding=ROUND_HALF_UP,
        )

        pass_percentage = (
            get_quiz_pass_percentage()
        )

        passed = (
            percentage
            >= pass_percentage
        )

        start_value = (
            request.session.get(
                start_key
            )
        )

        started_at = None

        if start_value:

            started_at = (
                parse_datetime(
                    start_value
                )
            )

        if started_at is None:

            started_at = (
                timezone.now()
            )

        completed_at = (
            timezone.now()
        )

        # -------------------------------------------------
        # Safely determine next attempt number
        # -------------------------------------------------

        with transaction.atomic():

            locked_assignment = (
                EmployeeTraining.objects
                .select_for_update()
                .get(
                    employee_training_id=(
                        assignment_id
                    ),
                    user=request.user,
                )
            )

            previous_attempt = (
                QuizAttempt.objects
                .filter(
                    assignment=(
                        locked_assignment
                    )
                )
                .aggregate(
                    highest=Max(
                        "attempt_number"
                    )
                )["highest"]
            )

            next_attempt_number = (
                (
                    previous_attempt
                    or 0
                )
                + 1
            )

            attempt = (
                QuizAttempt.objects.create(
                    assignment=(
                        locked_assignment
                    ),
                    attempt_number=(
                        next_attempt_number
                    ),
                    score=Decimal(
                        earned_marks
                    ),
                    percentage=(
                        percentage
                    ),
                    passed=passed,
                    started_at=(
                        started_at
                    ),
                    completed_at=(
                        completed_at
                    ),
                )
            )

        # -------------------------------------------------
        # Audit Log
        # -------------------------------------------------

        log_action(
            request=request,
            action=(
                "QUIZ_ATTEMPT_COMPLETED"
            ),
            entity_type=(
                "QuizAttempt"
            ),
            entity_id=(
                attempt.attempt_id
            ),
            details=(
                f"Employee "
                f"{request.user.staff_no} "
                f"completed quiz for "
                f"'{training.title}'. "
                f"Attempt "
                f"{attempt.attempt_number}, "
                f"Score "
                f"{attempt.percentage}%, "
                f"Passed: "
                f"{attempt.passed}."
            ),
        )

        # -------------------------------------------------
        # Remove one-time session values
        # -------------------------------------------------

        request.session.pop(
            start_key,
            None,
        )

        request.session.pop(
            token_key,
            None,
        )

        if passed:

            messages.success(
                request,
                (
                    "Quiz completed successfully. "
                    "You passed the assessment."
                ),
            )

        else:

            messages.warning(
                request,
                (
                    "Quiz completed. "
                    "You did not reach the "
                    "required pass mark."
                ),
            )

        return redirect(
            "training:employee_quiz_result",
            attempt_id=(
                attempt.attempt_id
            ),
        )


    # -----------------------------------------------------
    # DISPLAY QUIZ
    # -----------------------------------------------------

    previous_attempt_count = (
        QuizAttempt.objects.filter(
            assignment=assignment
        ).count()
    )

    return render(
        request,
        "employee/quiz/take.html",
        {
            "assignment": assignment,
            "training": training,
            "questions": questions,

            "total_marks": (
                total_marks
            ),

            "attempt_number": (
                previous_attempt_count
                + 1
            ),

            "quiz_token": (
                request.session.get(
                    token_key
                )
            ),

            "pass_percentage": (
                get_quiz_pass_percentage()
            ),
        },
    )


# =========================================================
# EMPLOYEE - QUIZ RESULT
# =========================================================

@role_required(Role.EMPLOYEE)
def employee_quiz_result(
    request,
    attempt_id,
):

    attempt = get_object_or_404(
        QuizAttempt.objects
        .select_related(
            "assignment",
            "assignment__training",
        ),
        attempt_id=attempt_id,
        assignment__user=(
            request.user
        ),
    )

    training = (
        attempt.assignment.training
    )

    total_marks = (
        QuizQuestion.objects
        .filter(
            training=training
        )
        .aggregate(
            total=Sum("marks")
        )["total"]
        or 0
    )

    return render(
        request,
        (
            "employee/"
            "quiz/result.html"
        ),
        {
            "attempt": attempt,
            "training": training,

            "total_marks": (
                total_marks
            ),

            "pass_percentage": (
                get_quiz_pass_percentage()
            ),
        },
    )