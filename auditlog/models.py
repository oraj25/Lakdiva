from django.conf import settings
from django.db import models


# =========================================================
# AUDIT LOG
# =========================================================

class AuditLog(models.Model):

    log_id = models.BigAutoField(
        primary_key=True
    )

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="audit_logs",
        db_column="user_id",
    )

    action = models.CharField(
        max_length=100
    )

    entity_type = models.CharField(
        max_length=100,
        blank=True,
    )

    entity_id = models.BigIntegerField(
        null=True,
        blank=True,
    )

    details = models.TextField(
        blank=True
    )

    ip_address = models.GenericIPAddressField(
        null=True,
        blank=True,
    )

    created_at = models.DateTimeField(
        auto_now_add=True,
    )


    class Meta:

        db_table = "audit_logs"

        ordering = [
            "-created_at"
        ]

        indexes = [

            models.Index(
                fields=[
                    "user"
                ]
            ),

            models.Index(
                fields=[
                    "entity_type"
                ]
            ),
        ]


    def __str__(self):

        actor = (
            self.user.staff_no
            if self.user
            else "SYSTEM"
        )

        return (
            f"{actor} - "
            f"{self.action} - "
            f"{self.created_at}"
        )