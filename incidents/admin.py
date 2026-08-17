from django.contrib import admin

from .models import (
    Incident,
    IncidentCategory,
    IncidentEvidence,
    IncidentRiskAssessment,
)


# =========================================================
# INCIDENT CATEGORIES
# =========================================================

@admin.register(IncidentCategory)
class IncidentCategoryAdmin(
    admin.ModelAdmin
):

    list_display = [
        "category_id",
        "category_name",
        "status",
        "created_at",
        "updated_at",
    ]

    list_filter = [
        "status",
    ]

    search_fields = [
        "category_name",
        "description",
    ]


# =========================================================
# INCIDENTS
# =========================================================

@admin.register(Incident)
class IncidentAdmin(
    admin.ModelAdmin
):

    list_display = [
        "incident_ref",
        "title",
        "reported_by",
        "category",
        "pos",
        "status",
        "created_at",
    ]

    list_filter = [
        "status",
        "category",
        "pos",
    ]

    search_fields = [
        "incident_ref",
        "title",
        "description",
        "reported_by__staff_no",
        "reported_by__full_name",
    ]

    readonly_fields = [
        "incident_ref",
        "reported_by",
        "category",
        "pos",
        "shift",
        "title",
        "description",
        "occurred_at",
        "status",
        "created_at",
        "resolved_at",
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
# INCIDENT EVIDENCE
# =========================================================

@admin.register(IncidentEvidence)
class IncidentEvidenceAdmin(
    admin.ModelAdmin
):

    list_display = [
        "evidence_id",
        "incident",
        "file_type",
        "uploaded_by",
        "uploaded_at",
    ]

    search_fields = [
        "incident__incident_ref",
        "uploaded_by__staff_no",
    ]

    readonly_fields = [
        "incident",
        "file",
        "file_type",
        "description",
        "uploaded_by",
        "uploaded_at",
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
# INCIDENT RISK ASSESSMENTS
# =========================================================

@admin.register(
    IncidentRiskAssessment
)
class IncidentRiskAssessmentAdmin(
    admin.ModelAdmin
):

    list_display = [
        "risk_id",
        "incident",
        "risk_score",
        "risk_level",
        "assessed_by",
        "assessed_at",
    ]

    list_filter = [
        "risk_level",
        "assessed_at",
    ]

    search_fields = [
        "incident__incident_ref",
        "incident__title",
        "assessed_by__staff_no",
        "assessed_by__full_name",
    ]

    ordering = [
        "-assessed_at"
    ]

    readonly_fields = [
        "incident",
        "customer_data_involved",
        "pos_affected",
        "unauthorized_access",
        "business_impact",
        "evidence_available",
        "risk_score",
        "risk_level",
        "assessed_by",
        "assessed_at",
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