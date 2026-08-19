from django.contrib import admin

from .models import (
    TrainingNeed,
)


@admin.register(TrainingNeed)
class TrainingNeedAdmin(
    admin.ModelAdmin
):

    list_display = [
        "need_id",
        "user",
        "training",
        "score",
        "priority",
        "status",
        "identified_at",
    ]

    list_filter = [
        "priority",
        "status",
    ]

    search_fields = [
        "user__staff_no",
        "user__full_name",
        "training__title",
    ]

    ordering = [
        "-identified_at"
    ]

    readonly_fields = [
        "user",
        "training",
        "score",
        "priority",
        "identified_at",
        "status",
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