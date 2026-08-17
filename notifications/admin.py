from django.contrib import admin

from .models import Notification


@admin.register(Notification)
class NotificationAdmin(
    admin.ModelAdmin
):

    list_display = [
        "notification_id",
        "user",
        "title",
        "notification_type",
        "is_read",
        "created_at",
    ]

    list_filter = [
        "notification_type",
        "is_read",
        "created_at",
    ]

    search_fields = [
        "user__staff_no",
        "user__full_name",
        "title",
        "message",
    ]

    ordering = [
        "-created_at"
    ]

    readonly_fields = [
        "user",
        "title",
        "message",
        "notification_type",
        "is_read",
        "created_at",
        "read_at",
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