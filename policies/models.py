from django.conf import settings
from django.core.exceptions import ValidationError
from django.db import models


# =========================================================
# POLICY MODEL
# =========================================================

class Policy(models.Model):

    # -----------------------------------------------------
    # POLICY STATUS
    # -----------------------------------------------------

    class Status(models.TextChoices):
        DRAFT = "Draft", "Draft"
        PUBLISHED = "Published", "Published"
        ARCHIVED = "Archived", "Archived"

    # -----------------------------------------------------
    # POLICY TYPES
    # -----------------------------------------------------

    class PolicyType(models.TextChoices):

        POS_SECURITY = (
            "POS Security",
            "POS Security"
        )

        PASSWORD_SECURITY = (
            "Password & Account Security",
            "Password & Account Security"
        )

        INCIDENT_REPORTING = (
            "Incident Reporting",
            "Incident Reporting"
        )

        DATA_PROTECTION = (
            "Data Protection & Privacy",
            "Data Protection & Privacy"
        )

        ACCEPTABLE_USE = (
            "Acceptable Use",
            "Acceptable Use Policy"
        )

        USB_SECURITY = (
            "Removable Media & USB Security",
            "Removable Media & USB Security"
        )

        SECURITY_TRAINING = (
            "Security Awareness & Training",
            "Security Awareness & Training"
        )

        ADMIN_ACCESS = (
            "Admin Access Control",
            "Admin Access Control"
        )

        POLICY_ADMINISTRATION = (
            "Policy Management & Administration",
            "Policy Management & Administration"
        )

        EMPLOYEE_DATA_ACCESS = (
            "Employee Data & Compliance Access",
            "Employee Data & Compliance Access"
        )

        AUDIT_MONITORING = (
            "Audit Log & Monitoring",
            "Audit Log & Monitoring"
        )

    # -----------------------------------------------------
    # DATABASE FIELDS
    # -----------------------------------------------------

    policy_id = models.BigAutoField(
        primary_key=True
    )

    title = models.CharField(
        max_length=200
    )

    policy_type = models.CharField(
        max_length=100,
        choices=PolicyType.choices,
        db_index=True,
    )

    version = models.CharField(
        max_length=20
    )

    content = models.TextField()

    effective_date = models.DateField(
        null=True,
        blank=True,
    )

    review_date = models.DateField(
        null=True,
        blank=True,
    )

    status = models.CharField(
        max_length=20,
        choices=Status.choices,
        default=Status.DRAFT,
        db_index=True,
    )

    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name="created_policies",
        db_column="created_by",
    )

    created_at = models.DateTimeField(
        auto_now_add=True
    )

    # -----------------------------------------------------
    # META
    # -----------------------------------------------------

    class Meta:
        db_table = "policies"

        ordering = [
            "title",
            "-created_at",
        ]

        constraints = [
            models.UniqueConstraint(
                fields=[
                    "title",
                    "version",
                ],
                name=(
                    "unique_policy_title_version"
                ),
            ),
        ]

        indexes = [
            models.Index(
                fields=["status"]
            ),
            models.Index(
                fields=["policy_type"]
            ),
        ]

    # -----------------------------------------------------
    # VALIDATION
    # -----------------------------------------------------

    def clean(self):

        super().clean()

        if (
            self.effective_date
            and self.review_date
            and self.review_date
            < self.effective_date
        ):
            raise ValidationError(
                {
                    "review_date": (
                        "Review date cannot be "
                        "before the effective date."
                    )
                }
            )

    def __str__(self):
        return (
            f"{self.title} "
            f"(v{self.version})"
        )


# =========================================================
# EMPLOYEE-VISIBLE POLICY TYPES
# =========================================================

EMPLOYEE_POLICY_TYPES = [
    Policy.PolicyType.POS_SECURITY,
    Policy.PolicyType.PASSWORD_SECURITY,
    Policy.PolicyType.INCIDENT_REPORTING,
    Policy.PolicyType.DATA_PROTECTION,
    Policy.PolicyType.ACCEPTABLE_USE,
    Policy.PolicyType.USB_SECURITY,
    Policy.PolicyType.SECURITY_TRAINING,
]


# =========================================================
# POLICY ACKNOWLEDGEMENT
# =========================================================

class PolicyAcknowledgement(models.Model):

    acknowledgement_id = models.BigAutoField(
        primary_key=True
    )

    policy = models.ForeignKey(
        Policy,
        on_delete=models.CASCADE,
        related_name="acknowledgements",
    )

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="policy_acknowledgements",
    )

    acknowledged_at = models.DateTimeField(
        auto_now_add=True
    )

    class Meta:
        db_table = "policy_acknowledgements"

        ordering = [
            "-acknowledged_at"
        ]

        constraints = [
            models.UniqueConstraint(
                fields=[
                    "policy",
                    "user",
                ],
                name=(
                    "unique_policy_user_acknowledgement"
                ),
            ),
        ]

    def __str__(self):
        return (
            f"{self.user.staff_no} - "
            f"{self.policy.title} "
            f"v{self.policy.version}"
        )