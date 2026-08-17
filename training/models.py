from django.conf import settings

from django.core.exceptions import (
    ValidationError,
)

from django.core.validators import (
    MaxValueValidator,
    MinValueValidator,
)

from django.db import models

# =========================================================
# TRAINING MODULE
# =========================================================

class TrainingModule(models.Model):

    # -----------------------------------------------------
    # STATUS
    # -----------------------------------------------------

    class Status(models.TextChoices):
        DRAFT = "Draft", "Draft"
        PUBLISHED = "Published", "Published"
        ARCHIVED = "Archived", "Archived"

    # -----------------------------------------------------
    # TRAINING TOPICS
    # -----------------------------------------------------

    class Topic(models.TextChoices):

        POS_SECURITY = (
            "POS Security",
            "POS Security",
        )

        PASSWORD_SECURITY = (
            "Password Security",
            "Password Security",
        )

        PHISHING = (
            "Phishing & Social Engineering",
            "Phishing & Social Engineering",
        )

        INCIDENT_REPORTING = (
            "Incident Reporting",
            "Incident Reporting",
        )

        DATA_PROTECTION = (
            "Data Protection",
            "Data Protection",
        )

        USB_SECURITY = (
            "Removable Media & USB Security",
            "Removable Media & USB Security",
        )

    # -----------------------------------------------------
    # DATABASE FIELDS
    # -----------------------------------------------------

    training_id = models.BigAutoField(
        primary_key=True
    )

    title = models.CharField(
        max_length=200
    )

    topic = models.CharField(
        max_length=100,
        choices=Topic.choices,
        db_index=True,
    )

    description = models.TextField(
        blank=True
    )

    content = models.TextField()

    status = models.CharField(
        max_length=20,
        choices=Status.choices,
        default=Status.DRAFT,
        db_index=True,
    )

    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name="created_training_modules",
        db_column="created_by",
    )

    created_at = models.DateTimeField(
        auto_now_add=True
    )

    class Meta:
        db_table = "training_modules"

        ordering = [
            "title"
        ]

        indexes = [
            models.Index(
                fields=["status"]
            ),
            models.Index(
                fields=["topic"]
            ),
        ]

    def __str__(self):
        return self.title


# =========================================================
# EMPLOYEE TRAINING
# =========================================================

class EmployeeTraining(models.Model):

    class Status(models.TextChoices):
        ASSIGNED = "Assigned", "Assigned"
        IN_PROGRESS = "In Progress", "In Progress"
        COMPLETED = "Completed", "Completed"

    employee_training_id = models.BigAutoField(
        primary_key=True
    )

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="employee_training",
        db_column="user_id",
    )

    training = models.ForeignKey(
        TrainingModule,
        on_delete=models.PROTECT,
        related_name="employee_assignments",
        db_column="training_id",
    )

    assigned_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name="training_assigned_by_me",
        db_column="assigned_by",
    )

    assigned_at = models.DateTimeField(
        auto_now_add=True
    )

    due_date = models.DateField(
        null=True,
        blank=True,
    )

    status = models.CharField(
        max_length=20,
        choices=Status.choices,
        default=Status.ASSIGNED,
        db_index=True,
    )

    progress_percent = models.PositiveSmallIntegerField(
        default=0,
        validators=[
            MinValueValidator(0),
            MaxValueValidator(100),
        ],
    )

    # These will be used in Step 9 - Quiz.
    score = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        null=True,
        blank=True,
    )

    passed = models.BooleanField(
        null=True,
        blank=True,
    )

    completed_at = models.DateTimeField(
        null=True,
        blank=True,
    )

    class Meta:

        db_table = "employee_training"

        ordering = [
            "-assigned_at"
        ]

        indexes = [
            models.Index(
                fields=["user"]
            ),
            models.Index(
                fields=["training"]
            ),
            models.Index(
                fields=["status"]
            ),
        ]

    def __str__(self):

        return (
            f"{self.user.staff_no} - "
            f"{self.training.title}"
        )


# =========================================================
# QUIZ QUESTION
# =========================================================

class QuizQuestion(models.Model):

    class CorrectOption(models.TextChoices):
        A = "A", "A"
        B = "B", "B"
        C = "C", "C"
        D = "D", "D"

    question_id = models.BigAutoField(
        primary_key=True
    )

    training = models.ForeignKey(
        TrainingModule,
        on_delete=models.CASCADE,
        related_name="quiz_questions",
        db_column="training_id",
    )

    question_text = models.TextField()

    option_a = models.CharField(
        max_length=500
    )

    option_b = models.CharField(
        max_length=500
    )

    option_c = models.CharField(
        max_length=500,
        blank=True,
    )

    option_d = models.CharField(
        max_length=500,
        blank=True,
    )

    correct_option = models.CharField(
        max_length=1,
        choices=CorrectOption.choices,
    )

    marks = models.PositiveIntegerField(
        default=1,
        validators=[
            MinValueValidator(1)
        ],
    )

    class Meta:

        db_table = "quiz_questions"

        ordering = [
            "question_id"
        ]

        indexes = [
            models.Index(
                fields=["training"]
            ),
        ]

    def clean(self):

        super().clean()

        if (
            self.correct_option
            == self.CorrectOption.C
            and not self.option_c
        ):
            raise ValidationError(
                {
                    "correct_option": (
                        "Option C cannot be the "
                        "correct answer because "
                        "Option C is empty."
                    )
                }
            )

        if (
            self.correct_option
            == self.CorrectOption.D
            and not self.option_d
        ):
            raise ValidationError(
                {
                    "correct_option": (
                        "Option D cannot be the "
                        "correct answer because "
                        "Option D is empty."
                    )
                }
            )

    def __str__(self):

        return (
            f"{self.training.title} - "
            f"Question {self.question_id}"
        )


# =========================================================
# QUIZ ATTEMPT
# =========================================================

class QuizAttempt(models.Model):

    attempt_id = models.BigAutoField(
        primary_key=True
    )

    assignment = models.ForeignKey(
        EmployeeTraining,
        on_delete=models.CASCADE,
        related_name="quiz_attempts",
        db_column="assignment_id",
    )

    attempt_number = models.PositiveIntegerField(
        default=1
    )

    # Raw marks earned
    score = models.DecimalField(
        max_digits=8,
        decimal_places=2,
    )

    percentage = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        validators=[
            MinValueValidator(0),
            MaxValueValidator(100),
        ],
    )

    passed = models.BooleanField()

    started_at = models.DateTimeField()

    completed_at = models.DateTimeField()

    class Meta:

        db_table = "quiz_attempts"

        ordering = [
            "-completed_at"
        ]

        constraints = [
            models.UniqueConstraint(
                fields=[
                    "assignment",
                    "attempt_number",
                ],
                name=(
                    "unique_assignment_attempt_number"
                ),
            ),
        ]

        indexes = [
            models.Index(
                fields=["assignment"]
            ),

            models.Index(
                fields=["passed"]
            ),
        ]

    def __str__(self):

        return (
            f"{self.assignment.user.staff_no} - "
            f"{self.assignment.training.title} - "
            f"Attempt {self.attempt_number}"
        )