from django.contrib import admin

from .models import (
    AuditLog,
)


@admin.register(AuditLog)
class AuditLogAdmin(
    admin.ModelAdmin
):

    list_display = [
        "log_id",
        "user",
        "action",
        "entity_type",
        "entity_id",
        "ip_address",
        "created_at",
    ]

    list_filter = [
        "action",
        "entity_type",
        "created_at",
    ]

    search_fields = [
        "user__staff_no",
        "user__full_name",
        "action",
        "entity_type",
        "details",
        "ip_address",
    ]

    ordering = [
        "-created_at"
    ]

    readonly_fields = [
        "user",
        "action",
        "entity_type",
        "entity_id",
        "details",
        "ip_address",
        "created_at",
    ]


    # -----------------------------------------------------
    # NO MANUAL CREATE
    # -----------------------------------------------------

    def has_add_permission(
        self,
        request,
    ):

        return False


    # -----------------------------------------------------
    # NO EDIT
    # -----------------------------------------------------

    def has_change_permission(
        self,
        request,
        obj=None,
    ):

        return False


    # -----------------------------------------------------
    # NO DELETE
    # -----------------------------------------------------

    def has_delete_permission(
        self,
        request,
        obj=None,
    ):

        return False