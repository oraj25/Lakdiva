from django.conf import settings

from django.db import models

from django.utils import timezone

from training.models import (
    TrainingModule,
)


# =========================================================
# TRAINING NEED
# =========================================================

class TrainingNeed(models.Model):

    # -----------------------------------------------------
    # PRIORITY
    # -----------------------------------------------------

    class Priority(models.TextChoices):

        LOW = (
            "Low",
            "Low",
        )

        MEDIUM = (
            "Medium",
            "Medium",
        )

        HIGH = (
            "High",
            "High",
        )


    # -----------------------------------------------------
    # STATUS
    # -----------------------------------------------------

    class Status(models.TextChoices):

        OPEN = (
            "Open",
            "Open",
        )

        ADDRESSED = (
            "Addressed",
            "Addressed",
        )


    # -----------------------------------------------------
    # DATABASE FIELDS
    # -----------------------------------------------------

    need_id = models.BigAutoField(
        primary_key=True
    )

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="training_needs",
        db_column="user_id",
    )

    training = models.ForeignKey(
        TrainingModule,
        on_delete=models.PROTECT,
        related_name="identified_training_needs",
        db_column="training_id",
    )

    score = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        null=True,
        blank=True,
    )

    priority = models.CharField(
        max_length=10,
        choices=Priority.choices,
        db_index=True,
    )

    identified_at = models.DateTimeField(
        default=timezone.now,
        db_index=True,
    )

    status = models.CharField(
        max_length=15,
        choices=Status.choices,
        default=Status.OPEN,
        db_index=True,
    )


    # -----------------------------------------------------
    # META
    # -----------------------------------------------------

    class Meta:

        db_table = "training_needs"

        ordering = [
            "-identified_at"
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

            models.Index(
                fields=["priority"]
            ),
        ]


    # -----------------------------------------------------
    # STRING
    # -----------------------------------------------------

    def __str__(self):

        return (
            f"{self.user.staff_no} - "
            f"{self.training.title} - "
            f"{self.priority}"
        )