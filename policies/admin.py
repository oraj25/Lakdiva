from django.contrib import admin

from .models import (
    Policy,
    PolicyAcknowledgement,
)


@admin.register(Policy)
class PolicyAdmin(admin.ModelAdmin):

    list_display = [
        "policy_id",
        "title",
        "policy_type",
        "version",
        "status",
        "effective_date",
        "review_date",
        "created_by",
        "created_at",
    ]

    list_filter = [
        "status",
        "policy_type",
    ]

    search_fields = [
        "title",
        "version",
        "content",
    ]

    ordering = [
        "title",
        "-created_at",
    ]


@admin.register(
    PolicyAcknowledgement
)
class PolicyAcknowledgementAdmin(
    admin.ModelAdmin
):

    list_display = [
        "acknowledgement_id",
        "policy",
        "user",
        "acknowledged_at",
    ]

    search_fields = [
        "policy__title",
        "user__staff_no",
        "user__full_name",
        "user__email",
    ]

    list_filter = [
        "acknowledged_at",
    ]

    readonly_fields = [
        "policy",
        "user",
        "acknowledged_at",
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