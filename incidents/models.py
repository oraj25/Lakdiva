from django.conf import settings

from django.db import models

from django.utils import timezone

from django.utils.text import (
    get_valid_filename,
)

from pos_security.models import (
    POSTerminal,
    POSShift,
)


# =========================================================
# INCIDENT EVIDENCE STORAGE PATH
# =========================================================

def incident_evidence_upload_path(
    instance,
    filename,
):

    safe_filename = (
        get_valid_filename(
            filename
        )
    )

    return (
        f"incident_evidence/"
        f"{instance.incident.incident_ref}/"
        f"{safe_filename}"
    )


# =========================================================
# INCIDENT CATEGORY
# =========================================================

class IncidentCategory(models.Model):

    class Status(models.TextChoices):
        ACTIVE = "Active", "Active"
        INACTIVE = "Inactive", "Inactive"

    category_id = models.BigAutoField(
        primary_key=True
    )

    category_name = models.CharField(
        max_length=100,
        unique=True,
    )

    description = models.TextField(
        blank=True
    )

    status = models.CharField(
        max_length=10,
        choices=Status.choices,
        default=Status.ACTIVE,
        db_index=True,
    )

    created_at = models.DateTimeField(
        auto_now_add=True
    )

    updated_at = models.DateTimeField(
        auto_now=True
    )

    class Meta:

        db_table = "incident_categories"

        ordering = [
            "category_name"
        ]

    @property
    def latest_risk_assessment(self):

        return (
            self.risk_assessments
            .order_by(
                "-assessed_at"
            )
            .first()
        )

    def __str__(self):

        return self.category_name


# =========================================================
# INCIDENT
# =========================================================

class Incident(models.Model):

    class Status(models.TextChoices):

        NEW = (
            "NEW",
            "New",
        )

        INVESTIGATING = (
            "INVESTIGATING",
            "Investigating",
        )

        RESOLVED = (
            "RESOLVED",
            "Resolved",
        )

    incident_id = models.BigAutoField(
        primary_key=True
    )

    incident_ref = models.CharField(
        max_length=50,
        unique=True,
    )

    reported_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name="reported_incidents",
        db_column="reported_by",
    )

    category = models.ForeignKey(
        IncidentCategory,
        on_delete=models.PROTECT,
        related_name="incidents",
        db_column="category_id",
    )

    pos = models.ForeignKey(
        POSTerminal,
        on_delete=models.PROTECT,
        null=True,
        blank=True,
        related_name="incidents",
        db_column="pos_id",
    )

    shift = models.ForeignKey(
        POSShift,
        on_delete=models.PROTECT,
        null=True,
        blank=True,
        related_name="incidents",
        db_column="shift_id",
    )

    title = models.CharField(
        max_length=200
    )

    description = models.TextField()

    occurred_at = models.DateTimeField(
        null=True,
        blank=True,
    )

    status = models.CharField(
        max_length=20,
        choices=Status.choices,
        default=Status.NEW,
        db_index=True,
    )

    created_at = models.DateTimeField(
        default=timezone.now,
        db_index=True,
    )

    resolved_at = models.DateTimeField(
        null=True,
        blank=True,
    )

    class Meta:

        db_table = "incidents"

        ordering = [
            "-created_at"
        ]

        indexes = [
            models.Index(
                fields=[
                    "reported_by"
                ]
            ),

            models.Index(
                fields=[
                    "category"
                ]
            ),

            models.Index(
                fields=[
                    "status"
                ]
            ),
        ]

    def __str__(self):

        return (
            f"{self.incident_ref} - "
            f"{self.title}"
        )


# =========================================================
# INCIDENT EVIDENCE
# =========================================================

class IncidentEvidence(models.Model):

    class FileType(models.TextChoices):

        IMAGE = "Image", "Image"

        DOCUMENT = (
            "Document",
            "Document",
        )

        LOG = "Log", "Log"

        OTHER = "Other", "Other"

    evidence_id = models.BigAutoField(
        primary_key=True
    )

    incident = models.ForeignKey(
        Incident,
        on_delete=models.CASCADE,
        related_name="evidence_files",
        db_column="incident_id",
    )

    file = models.FileField(
        upload_to=(
            incident_evidence_upload_path
        ),
        db_column="file_path",
    )

    file_type = models.CharField(
        max_length=30,
        choices=FileType.choices,
        default=FileType.OTHER,
    )

    description = models.CharField(
        max_length=255,
        blank=True,
    )

    uploaded_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name="uploaded_incident_evidence",
        db_column="uploaded_by",
    )

    uploaded_at = models.DateTimeField(
        auto_now_add=True
    )

    class Meta:

        db_table = "incident_evidence"

        ordering = [
            "uploaded_at"
        ]

        indexes = [
            models.Index(
                fields=[
                    "incident"
                ]
            ),
        ]

    def __str__(self):

        return (
            f"Evidence {self.evidence_id} - "
            f"{self.incident.incident_ref}"
        )

# =========================================================
# INCIDENT RISK ASSESSMENT
# =========================================================

class IncidentRiskAssessment(models.Model):

    # -----------------------------------------------------
    # RISK LEVEL
    # -----------------------------------------------------

    class RiskLevel(models.TextChoices):

        LOW = "LOW", "Low"

        MEDIUM = "MEDIUM", "Medium"

        HIGH = "HIGH", "High"


    # -----------------------------------------------------
    # BUSINESS IMPACT
    # -----------------------------------------------------

    class BusinessImpact(
        models.IntegerChoices
    ):

        NO_IMPACT = (
            0,
            "No significant business impact"
        )

        BUSINESS_AFFECTED = (
            2,
            "Business operations affected"
        )


    # -----------------------------------------------------
    # DATABASE FIELDS
    # -----------------------------------------------------

    risk_id = models.BigAutoField(
        primary_key=True
    )

    incident = models.ForeignKey(
        Incident,
        on_delete=models.CASCADE,
        related_name="risk_assessments",
        db_column="incident_id",
    )

    customer_data_involved = (
        models.BooleanField()
    )

    pos_affected = (
        models.BooleanField()
    )

    unauthorized_access = (
        models.BooleanField()
    )

    business_impact = (
        models.PositiveSmallIntegerField(
            choices=(
                BusinessImpact.choices
            )
        )
    )

    evidence_available = (
        models.BooleanField()
    )

    risk_score = (
        models.PositiveSmallIntegerField(
            editable=False
        )
    )

    risk_level = models.CharField(
        max_length=10,
        choices=RiskLevel.choices,
        editable=False,
        db_index=True,
    )

    assessed_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name=(
            "incident_risk_assessments"
        ),
        db_column="assessed_by",
    )

    assessed_at = models.DateTimeField(
        auto_now_add=True,
        db_index=True,
    )


    # -----------------------------------------------------
    # META
    # -----------------------------------------------------

    class Meta:

        db_table = (
            "incident_risk_assessments"
        )

        ordering = [
            "-assessed_at"
        ]

        indexes = [

            models.Index(
                fields=["incident"]
            ),

            models.Index(
                fields=["risk_level"]
            ),
        ]

        constraints = [

            models.CheckConstraint(
                condition=models.Q(
                    business_impact__in=[
                        0,
                        2,
                    ]
                ),
                name=(
                    "valid_incident_"
                    "business_impact"
                ),
            ),

            models.CheckConstraint(
                condition=models.Q(
                    risk_score__gte=0,
                    risk_score__lte=12,
                ),
                name=(
                    "valid_incident_"
                    "risk_score"
                ),
            ),
        ]


    # -----------------------------------------------------
    # SCORE CALCULATION
    # -----------------------------------------------------

    def calculate_score(self):

        score = 0

        if self.customer_data_involved:
            score += 3

        if self.pos_affected:
            score += 3

        if self.unauthorized_access:
            score += 3

        score += self.business_impact

        if self.evidence_available:
            score += 1

        return score


    # -----------------------------------------------------
    # RISK CLASSIFICATION
    # -----------------------------------------------------

    @classmethod
    def classify_score(
        cls,
        score,
    ):

        if score <= 4:

            return (
                cls.RiskLevel.LOW
            )

        if score <= 7:

            return (
                cls.RiskLevel.MEDIUM
            )

        return cls.RiskLevel.HIGH


    # -----------------------------------------------------
    # SAVE
    # -----------------------------------------------------

    def save(
        self,
        *args,
        **kwargs,
    ):

        self.risk_score = (
            self.calculate_score()
        )

        self.risk_level = (
            self.classify_score(
                self.risk_score
            )
        )

        super().save(
            *args,
            **kwargs
        )


    def __str__(self):

        return (
            f"{self.incident.incident_ref} "
            f"- {self.risk_level} "
            f"({self.risk_score}/12)"
        )