from django.conf import settings
from django.db import models


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
        db_index=True,
    )

    class Meta:
        db_table = "audit_logs"
        ordering = ["-created_at"]

    def __str__(self):
        return (
            f"{self.action} - "
            f"{self.created_at}"
        )