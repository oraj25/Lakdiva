from django.conf import settings
from django.db import models


class Notification(models.Model):

    class NotificationType(models.TextChoices):

        NEW_INCIDENT = (
            "NEW_INCIDENT",
            "New Incident",
        )

        HIGH_RISK_INCIDENT = (
            "HIGH_RISK_INCIDENT",
            "High Risk Incident",
        )

        POLICY = (
            "POLICY",
            "Policy",
        )

        TRAINING = (
            "TRAINING",
            "Training",
        )

        COMPLIANCE = (
            "COMPLIANCE",
            "Compliance",
        )

        OTHER = (
            "OTHER",
            "Other",
        )

    notification_id = models.BigAutoField(
        primary_key=True
    )

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="notifications",
        db_column="user_id",
    )

    title = models.CharField(
        max_length=200
    )

    message = models.TextField()

    notification_type = models.CharField(
        max_length=50,
        choices=NotificationType.choices,
        db_index=True,
    )

    is_read = models.BooleanField(
        default=False,
        db_index=True,
    )

    created_at = models.DateTimeField(
        auto_now_add=True
    )

    read_at = models.DateTimeField(
        null=True,
        blank=True,
    )

    class Meta:

        db_table = "notifications"

        ordering = [
            "-created_at"
        ]

        indexes = [
            models.Index(
                fields=[
                    "user",
                    "is_read",
                ]
            ),
        ]

    def __str__(self):

        return (
            f"{self.user.staff_no} - "
            f"{self.title}"
        )