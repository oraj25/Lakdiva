from django.contrib import admin

from .models import (
    DailySecurityCheck,
    POSTerminal,
    POSShift,
)


# =========================================================
# POS TERMINALS
# =========================================================

@admin.register(POSTerminal)
class POSTerminalAdmin(
    admin.ModelAdmin
):

    list_display = [
        "pos_id",
        "terminal_code",
        "status",
        "created_at",
        "updated_at",
    ]

    list_filter = [
        "status",
    ]

    search_fields = [
        "terminal_code",
    ]


# =========================================================
# POS SHIFTS
# =========================================================

@admin.register(POSShift)
class POSShiftAdmin(
    admin.ModelAdmin
):

    list_display = [
        "shift_id",
        "user",
        "pos",
        "shift_start",
        "shift_end",
        "status",
        "cash_variance",
    ]

    list_filter = [
        "status",
        "pos",
    ]

    search_fields = [
        "user__staff_no",
        "user__full_name",
        "pos__terminal_code",
    ]

    readonly_fields = [
        "user",
        "pos",
        "shift_start",
        "shift_end",
        "opening_cash",
        "cash_in",
        "cash_out",
        "closing_cash",
        "cash_variance",
        "handed_over_to",
        "handover_time",
        "handover_notes",
        "status",
        "created_at",
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
# SECURITY CHECK
# =========================================================

@admin.register(
    DailySecurityCheck
)
class DailySecurityCheckAdmin(
    admin.ModelAdmin
):

    list_display = [
        "check_id",
        "shift",
        "result",
        "checked_at",
    ]

    list_filter = [
        "result",
    ]

    readonly_fields = [
        "shift",
        "is_unknown_device_present",
        "is_unusual_behavior_observed",
        "is_physically_secure",
        "is_credentials_secure",
        "is_suspicious_surroundings",
        "result",
        "comments",
        "checked_at",
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