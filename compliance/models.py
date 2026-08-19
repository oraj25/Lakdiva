from django.conf import settings
from django.db import models
from django.utils import timezone


# =========================================================
# COMPLIANCE SUMMARY
# =========================================================

class ComplianceSummary(models.Model):

    compliance_id = models.BigAutoField(
        primary_key=True
    )

    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="compliance_summary",
        db_column="user_id",
    )

    policy_compliance = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        default=0,
    )

    training_compliance = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        default=0,
    )

    pos_check_compliance = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        default=0,
    )

    employee_score = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        default=0,
    )

    last_calculated_at = models.DateTimeField(
        default=timezone.now,
    )

    class Meta:

        db_table = "compliance_summary"

        ordering = [
            "-employee_score"
        ]

    def __str__(self):

        return (
            f"{self.user.staff_no} - "
            f"{self.employee_score}%"
        )